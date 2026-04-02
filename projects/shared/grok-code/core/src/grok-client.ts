/**
 * Grok Code - Core API Client
 * 
 * Provides streaming chat completions with tool use support,
 * truth-seeking confidence scoring, and rate limiting.
 */

import { EventEmitter } from 'events';

export interface GrokConfig {
  apiKey: string;
  baseUrl?: string;
  model?: string;
  maxRetries?: number;
  timeout?: number;
}

export interface Message {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  tool_call_id?: string;
  tool_calls?: ToolCall[];
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface Tool {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
  };
}

export interface GrokResponse {
  content: string;
  confidence: number;
  tool_calls?: ToolCall[];
  finish_reason: string;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface StreamChunk {
  type: 'content' | 'tool_call' | 'done' | 'error';
  content?: string;
  tool_call?: ToolCall;
  error?: string;
}

const DEFAULT_CONFIG: Partial<GrokConfig> = {
  baseUrl: 'https://api.x.ai/v1',
  model: 'grok-3-latest',
  maxRetries: 3,
  timeout: 120000,
};

export class GrokClient extends EventEmitter {
  private config: Required<GrokConfig>;
  private conversationHistory: Message[] = [];

  constructor(config: GrokConfig) {
    super();
    this.config = { ...DEFAULT_CONFIG, ...config } as Required<GrokConfig>;
  }

  /**
   * Send a message and get a response (non-streaming)
   */
  async chat(
    messages: Message[],
    options?: {
      tools?: Tool[];
      temperature?: number;
      maxTokens?: number;
    }
  ): Promise<GrokResponse> {
    const response = await this.makeRequest('/chat/completions', {
      model: this.config.model,
      messages,
      tools: options?.tools,
      temperature: options?.temperature ?? 0.7,
      max_tokens: options?.maxTokens ?? 4096,
    });

    const choice = response.choices[0];
    const content = choice.message.content || '';

    // Calculate confidence based on response characteristics
    const confidence = this.calculateConfidence(content, choice);

    return {
      content,
      confidence,
      tool_calls: choice.message.tool_calls,
      finish_reason: choice.finish_reason,
      usage: response.usage,
    };
  }

  /**
   * Stream a response with real-time chunks
   */
  async *stream(
    messages: Message[],
    options?: {
      tools?: Tool[];
      temperature?: number;
      maxTokens?: number;
    }
  ): AsyncGenerator<StreamChunk> {
    const response = await fetch(`${this.config.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.config.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: this.config.model,
        messages,
        tools: options?.tools,
        temperature: options?.temperature ?? 0.7,
        max_tokens: options?.maxTokens ?? 4096,
        stream: true,
      }),
    });

    if (!response.ok) {
      yield { type: 'error', error: `HTTP ${response.status}` };
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      yield { type: 'error', error: 'No response body' };
      return;
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            yield { type: 'done' };
            return;
          }

          try {
            const parsed = JSON.parse(data);
            const delta = parsed.choices?.[0]?.delta;
            
            if (delta?.content) {
              yield { type: 'content', content: delta.content };
            }
            
            if (delta?.tool_calls) {
              for (const tc of delta.tool_calls) {
                yield { type: 'tool_call', tool_call: tc };
              }
            }
          } catch {
            // Skip malformed chunks
          }
        }
      }
    }

    yield { type: 'done' };
  }

  /**
   * Execute a tool-using conversation loop
   */
  async runWithTools(
    prompt: string,
    tools: Tool[],
    toolExecutor: (name: string, args: Record<string, unknown>) => Promise<string>,
    options?: {
      maxIterations?: number;
      systemPrompt?: string;
    }
  ): Promise<{ content: string; toolResults: Array<{ tool: string; result: string }> }> {
    const maxIterations = options?.maxIterations ?? 10;
    const toolResults: Array<{ tool: string; result: string }> = [];
    
    const messages: Message[] = [];
    
    if (options?.systemPrompt) {
      messages.push({ role: 'system', content: options.systemPrompt });
    }
    
    messages.push({ role: 'user', content: prompt });

    for (let i = 0; i < maxIterations; i++) {
      const response = await this.chat(messages, { tools });

      if (response.tool_calls && response.tool_calls.length > 0) {
        // Add assistant message with tool calls
        messages.push({
          role: 'assistant',
          content: response.content,
          tool_calls: response.tool_calls,
        });

        // Execute each tool
        for (const toolCall of response.tool_calls) {
          const args = JSON.parse(toolCall.function.arguments);
          const result = await toolExecutor(toolCall.function.name, args);
          
          toolResults.push({ tool: toolCall.function.name, result });
          
          messages.push({
            role: 'tool',
            tool_call_id: toolCall.id,
            content: result,
          });
        }
      } else {
        // No more tool calls, return final response
        return { content: response.content, toolResults };
      }
    }

    // Hit max iterations
    return {
      content: 'Max tool iterations reached',
      toolResults,
    };
  }

  /**
   * Calculate confidence score based on response characteristics
   * This is Grok's truth-seeking differentiator
   */
  private calculateConfidence(content: string, choice: any): number {
    let confidence = 0.8; // Base confidence

    // Reduce confidence for hedging language
    const hedgingPhrases = [
      'i think', 'maybe', 'possibly', 'might', 'could be',
      'not sure', 'uncertain', "i'm not certain", 'perhaps',
      'it seems', 'appears to be', 'likely'
    ];
    
    const lowerContent = content.toLowerCase();
    for (const phrase of hedgingPhrases) {
      if (lowerContent.includes(phrase)) {
        confidence -= 0.05;
      }
    }

    // Increase confidence for citations/sources
    if (content.includes('according to') || content.includes('based on')) {
      confidence += 0.1;
    }

    // Increase confidence for code blocks (verifiable)
    if (content.includes('```')) {
      confidence += 0.05;
    }

    // Reduce for very long responses (might be padding)
    if (content.length > 3000) {
      confidence -= 0.05;
    }

    // Clamp to 0-1
    return Math.max(0, Math.min(1, confidence));
  }

  /**
   * Make a request with retry logic
   */
  private async makeRequest(endpoint: string, body: Record<string, unknown>): Promise<any> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < this.config.maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

        const response = await fetch(`${this.config.baseUrl}${endpoint}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.config.apiKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(body),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const error = await response.text();
          throw new Error(`HTTP ${response.status}: ${error}`);
        }

        return response.json();
      } catch (error) {
        lastError = error as Error;
        
        // Exponential backoff
        if (attempt < this.config.maxRetries - 1) {
          await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1000));
        }
      }
    }

    throw lastError;
  }

  /**
   * Add to conversation history
   */
  addToHistory(message: Message): void {
    this.conversationHistory.push(message);
  }

  /**
   * Get conversation history
   */
  getHistory(): Message[] {
    return [...this.conversationHistory];
  }

  /**
   * Clear conversation history
   */
  clearHistory(): void {
    this.conversationHistory = [];
  }
}

export default GrokClient;
