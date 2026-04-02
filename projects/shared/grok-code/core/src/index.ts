/**
 * Grok Code - Core Library
 * 
 * AI coding agent powered by Grok with truth-seeking behavior
 * 
 * @example
 * ```typescript
 * import { GrokClient, AgentOrchestrator, getAllTools } from '@grok-code/core';
 * 
 * const client = new GrokClient({ apiKey: process.env.XAI_API_KEY });
 * const orchestrator = new AgentOrchestrator(client, { workdir: '/my/project' });
 * 
 * // Run a coding task
 * const result = await orchestrator.execute({
 *   id: 'task-1',
 *   description: 'Add user authentication',
 *   prompt: 'Implement JWT authentication for the Express API',
 *   agents: [
 *     { type: 'coder' },
 *     { type: 'reviewer', contrarian: true },
 *   ],
 *   workflow: 'review',
 * });
 * ```
 */

// Core client
export { GrokClient } from './grok-client';
export type {
  GrokConfig,
  Message,
  ToolCall,
  Tool,
  GrokResponse,
  StreamChunk,
} from './grok-client';

// Tools
export {
  executeTool,
  getAllTools,
  getToolsByCategory,
  formatToolResult,
  fileRead,
  fileWrite,
  fileEdit,
  fileTools,
  bashExecute,
  bashGetTaskOutput,
  bashStopTask,
  bashTools,
  grep,
  globSearch,
  webSearch,
  webFetch,
  searchTools,
} from './tools';
export type { ToolExecutorConfig, ToolResult } from './tools';

// Agents
export { AgentOrchestrator } from './agents/orchestrator';
export type {
  AgentType,
  AgentConfig,
  Task,
  AgentResult,
  OrchestratorResult,
} from './agents/orchestrator';

// Version
export const VERSION = '0.1.0';
