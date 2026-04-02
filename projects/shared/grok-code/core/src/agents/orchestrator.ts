/**
 * Grok Code - Agent Orchestrator
 * 
 * Multi-agent system for complex coding tasks with truth-seeking behavior
 */

import { GrokClient, Tool, Message } from '../grok-client';
import { executeTool, getAllTools, ToolExecutorConfig } from '../tools';

export type AgentType = 'coder' | 'reviewer' | 'tester' | 'docs' | 'security' | 'refactor';

export interface AgentConfig {
  type: AgentType;
  model?: string;
  temperature?: number;
  systemPrompt?: string;
  truthThreshold?: number;
  contrarian?: boolean;
}

export interface Task {
  id: string;
  description: string;
  prompt: string;
  agents: AgentConfig[];
  workflow: 'sequential' | 'parallel' | 'review';
  context?: Record<string, unknown>;
}

export interface AgentResult {
  agentType: AgentType;
  content: string;
  confidence: number;
  toolsUsed: string[];
  issues?: string[];
  suggestions?: string[];
}

export interface OrchestratorResult {
  taskId: string;
  success: boolean;
  results: AgentResult[];
  finalOutput: string;
  consensusConfidence: number;
}

const AGENT_PROMPTS: Record<AgentType, string> = {
  coder: `You are a senior software engineer. Write clean, efficient, well-documented code.
Focus on:
- Following best practices and design patterns
- Writing maintainable and testable code
- Proper error handling
- Clear variable and function names
Be direct and implement what's asked. If something is unclear, state your assumptions.`,

  reviewer: `You are a code reviewer with a critical eye for quality.
Your job is to:
- Find bugs, edge cases, and potential issues
- Suggest improvements for readability and performance
- Check for security vulnerabilities
- Verify the code matches requirements
Be thorough and specific in your feedback. Cite line numbers when relevant.`,

  tester: `You are a QA engineer specializing in test development.
Your responsibilities:
- Write comprehensive unit tests
- Cover edge cases and error conditions
- Create integration tests where needed
- Ensure tests are maintainable and clear
Use appropriate testing frameworks for the language.`,

  docs: `You are a technical writer creating developer documentation.
Focus on:
- Clear, concise explanations
- Practical examples
- API reference documentation
- README files and guides
Write for the intended audience - be detailed for complex topics, brief for simple ones.`,

  security: `You are a security engineer auditing code for vulnerabilities.
Check for:
- Input validation issues
- Injection vulnerabilities (SQL, XSS, etc.)
- Authentication/authorization flaws
- Sensitive data exposure
- Insecure dependencies
Provide specific recommendations with severity ratings.`,

  refactor: `You are a software architect focused on code improvement.
Your goals:
- Simplify complex logic
- Reduce code duplication
- Improve performance
- Enhance maintainability
- Apply appropriate design patterns
Explain the reasoning behind each refactoring suggestion.`,
};

const CONTRARIAN_SUFFIX = `
Additionally, you should:
- Challenge assumptions in the code or requirements
- Suggest alternative approaches
- Point out potential long-term issues
- Question if this is the right solution to the problem
Be constructive but don't accept things at face value.`;

export class AgentOrchestrator {
  private client: GrokClient;
  private toolConfig: ToolExecutorConfig;

  constructor(client: GrokClient, toolConfig: ToolExecutorConfig) {
    this.client = client;
    this.toolConfig = toolConfig;
  }

  /**
   * Execute a multi-agent task
   */
  async execute(task: Task): Promise<OrchestratorResult> {
    const results: AgentResult[] = [];
    let context = task.context || {};

    switch (task.workflow) {
      case 'sequential':
        // Each agent builds on the previous
        for (const agentConfig of task.agents) {
          const result = await this.runAgent(agentConfig, task.prompt, context);
          results.push(result);
          // Add result to context for next agent
          context = {
            ...context,
            [`${agentConfig.type}_output`]: result.content,
            [`${agentConfig.type}_confidence`]: result.confidence,
          };
        }
        break;

      case 'parallel':
        // Run all agents simultaneously
        const promises = task.agents.map(config =>
          this.runAgent(config, task.prompt, context)
        );
        const parallelResults = await Promise.all(promises);
        results.push(...parallelResults);
        break;

      case 'review':
        // Coder creates, reviewer critiques, coder revises
        const coderConfig = task.agents.find(a => a.type === 'coder');
        const reviewerConfig = task.agents.find(a => a.type === 'reviewer');

        if (!coderConfig || !reviewerConfig) {
          throw new Error('Review workflow requires coder and reviewer agents');
        }

        // Initial implementation
        const initial = await this.runAgent(coderConfig, task.prompt, context);
        results.push(initial);

        // Review
        const reviewPrompt = `Review this code:\n\n${initial.content}\n\nOriginal task: ${task.prompt}`;
        const review = await this.runAgent(reviewerConfig, reviewPrompt, context);
        results.push(review);

        // Revision if issues found
        if (review.issues && review.issues.length > 0) {
          const revisionPrompt = `Revise this code based on the review feedback:\n\nOriginal code:\n${initial.content}\n\nReview feedback:\n${review.content}`;
          const revision = await this.runAgent(coderConfig, revisionPrompt, context);
          results.push(revision);
        }
        break;
    }

    // Calculate consensus confidence
    const confidences = results.map(r => r.confidence);
    const consensusConfidence = confidences.reduce((a, b) => a + b, 0) / confidences.length;

    // Generate final output
    const finalOutput = this.synthesizeResults(task, results);

    return {
      taskId: task.id,
      success: consensusConfidence > 0.6,
      results,
      finalOutput,
      consensusConfidence,
    };
  }

  /**
   * Run a single agent
   */
  private async runAgent(
    config: AgentConfig,
    prompt: string,
    context: Record<string, unknown>
  ): Promise<AgentResult> {
    let systemPrompt = config.systemPrompt || AGENT_PROMPTS[config.type];
    
    if (config.contrarian) {
      systemPrompt += CONTRARIAN_SUFFIX;
    }

    // Add context to prompt
    let fullPrompt = prompt;
    if (Object.keys(context).length > 0) {
      fullPrompt += `\n\nContext from previous steps:\n${JSON.stringify(context, null, 2)}`;
    }

    const tools = getAllTools();
    const toolsUsed: string[] = [];

    // Execute with tool support
    const { content, toolResults } = await this.client.runWithTools(
      fullPrompt,
      tools,
      async (name, args) => {
        toolsUsed.push(name);
        const result = await executeTool(name, args, this.toolConfig);
        return result.success ? result.output : `Error: ${result.error}`;
      },
      { systemPrompt }
    );

    // Parse for issues and suggestions
    const issues = this.extractIssues(content);
    const suggestions = this.extractSuggestions(content);

    // Calculate confidence based on response
    const confidence = this.calculateAgentConfidence(content, config);

    return {
      agentType: config.type,
      content,
      confidence,
      toolsUsed,
      issues: issues.length > 0 ? issues : undefined,
      suggestions: suggestions.length > 0 ? suggestions : undefined,
    };
  }

  /**
   * Extract issues from agent output
   */
  private extractIssues(content: string): string[] {
    const issues: string[] = [];
    const patterns = [
      /(?:issue|bug|problem|error|vulnerability|flaw):\s*(.+)/gi,
      /(?:⚠️|❌|🔴)\s*(.+)/g,
      /- \[ \]\s*(.+)/g, // Unchecked todos often indicate issues
    ];

    for (const pattern of patterns) {
      let match;
      while ((match = pattern.exec(content)) !== null) {
        issues.push(match[1].trim());
      }
    }

    return [...new Set(issues)]; // Dedupe
  }

  /**
   * Extract suggestions from agent output
   */
  private extractSuggestions(content: string): string[] {
    const suggestions: string[] = [];
    const patterns = [
      /(?:suggest|recommend|consider|could|should|might want to):\s*(.+)/gi,
      /(?:💡|✨|📝)\s*(.+)/g,
    ];

    for (const pattern of patterns) {
      let match;
      while ((match = pattern.exec(content)) !== null) {
        suggestions.push(match[1].trim());
      }
    }

    return [...new Set(suggestions)];
  }

  /**
   * Calculate confidence for agent output
   */
  private calculateAgentConfidence(content: string, config: AgentConfig): number {
    let confidence = 0.75;

    // Reduce for uncertainty language
    const uncertainPhrases = ['not sure', 'might', 'possibly', 'unclear', 'depends'];
    for (const phrase of uncertainPhrases) {
      if (content.toLowerCase().includes(phrase)) {
        confidence -= 0.05;
      }
    }

    // Increase for concrete output
    if (content.includes('```')) confidence += 0.1; // Code blocks
    if (content.includes('function') || content.includes('class')) confidence += 0.05;
    
    // Decrease for very short responses
    if (content.length < 100) confidence -= 0.1;

    // Reviewer agents naturally have lower confidence (they find problems)
    if (config.type === 'reviewer' || config.type === 'security') {
      confidence -= 0.05;
    }

    return Math.max(0, Math.min(1, confidence));
  }

  /**
   * Synthesize results into final output
   */
  private synthesizeResults(task: Task, results: AgentResult[]): string {
    const parts: string[] = [];

    parts.push(`# Task: ${task.description}\n`);

    for (const result of results) {
      parts.push(`## ${result.agentType.charAt(0).toUpperCase() + result.agentType.slice(1)} Agent`);
      parts.push(`Confidence: ${(result.confidence * 100).toFixed(0)}%`);
      
      if (result.toolsUsed.length > 0) {
        parts.push(`Tools used: ${result.toolsUsed.join(', ')}`);
      }

      parts.push('\n' + result.content);

      if (result.issues) {
        parts.push('\n### Issues Found:');
        result.issues.forEach(i => parts.push(`- ${i}`));
      }

      if (result.suggestions) {
        parts.push('\n### Suggestions:');
        result.suggestions.forEach(s => parts.push(`- ${s}`));
      }

      parts.push('\n---\n');
    }

    return parts.join('\n');
  }

  /**
   * Quick single-agent execution
   */
  async runSingleAgent(
    type: AgentType,
    prompt: string,
    options?: Partial<AgentConfig>
  ): Promise<AgentResult> {
    const config: AgentConfig = {
      type,
      ...options,
    };

    return this.runAgent(config, prompt, {});
  }
}

export default AgentOrchestrator;
