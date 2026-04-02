/**
 * Grok Code - Tool Registry
 * 
 * Central registry and executor for all tools
 */

import { Tool } from '../grok-client';
import { fileRead, fileWrite, fileEdit, fileTools } from './file-ops';
import { bashExecute, bashGetTaskOutput, bashStopTask, bashTools } from './bash';
import { grep, globSearch, webSearch, webFetch, searchTools } from './search';

export interface ToolExecutorConfig {
  workdir: string;
  braveApiKey?: string;
  sandboxMode?: boolean;
}

export type ToolResult = {
  success: boolean;
  output: string;
  error?: string;
};

/**
 * Execute a tool by name with given arguments
 */
export async function executeTool(
  name: string,
  args: Record<string, unknown>,
  config: ToolExecutorConfig
): Promise<ToolResult> {
  try {
    let output: string;

    switch (name) {
      // File operations
      case 'file_read':
        output = await fileRead(args as any, config.workdir);
        break;

      case 'file_write':
        output = await fileWrite(args as any, config.workdir);
        break;

      case 'file_edit':
        output = await fileEdit(args as any, config.workdir);
        break;

      // Bash operations
      case 'bash':
        const bashResult = await bashExecute(args as any, config.workdir);
        if (bashResult.exitCode !== 0 && bashResult.exitCode !== null) {
          output = bashResult.stderr || bashResult.stdout || 'Command failed';
        } else {
          output = bashResult.stdout || bashResult.stderr || 'Command completed';
        }
        if (bashResult.taskId) {
          output = `Background task started: ${bashResult.taskId}\n${output}`;
        }
        if (bashResult.timedOut) {
          output += '\n(Command timed out)';
        }
        break;

      case 'task_output':
        const taskResult = await bashGetTaskOutput(args.task_id as string);
        output = taskResult.stdout || taskResult.stderr || 'No output yet';
        break;

      case 'task_stop':
        output = await bashStopTask(args.task_id as string);
        break;

      // Search operations
      case 'grep':
        output = await grep(args as any, config.workdir);
        break;

      case 'glob':
        output = await globSearch(args as any, config.workdir);
        break;

      case 'web_search':
        output = await webSearch(args as any, config.braveApiKey);
        break;

      case 'web_fetch':
        output = await webFetch(args.url as string, args.prompt as string);
        break;

      default:
        return {
          success: false,
          output: '',
          error: `Unknown tool: ${name}`,
        };
    }

    return { success: true, output };
  } catch (error: any) {
    return {
      success: false,
      output: '',
      error: error.message || String(error),
    };
  }
}

/**
 * Get all available tool definitions
 */
export function getAllTools(): Tool[] {
  return [
    ...fileTools,
    ...bashTools,
    ...searchTools,
  ];
}

/**
 * Get tools by category
 */
export function getToolsByCategory(category: 'file' | 'bash' | 'search'): Tool[] {
  switch (category) {
    case 'file':
      return fileTools;
    case 'bash':
      return bashTools;
    case 'search':
      return searchTools;
    default:
      return [];
  }
}

/**
 * Format tool result for display
 */
export function formatToolResult(result: ToolResult, toolName: string): string {
  if (result.success) {
    return result.output;
  } else {
    return `Error executing ${toolName}: ${result.error}`;
  }
}

export {
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
};
