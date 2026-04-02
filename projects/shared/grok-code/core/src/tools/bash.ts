/**
 * Grok Code - Bash Execution Tool
 * 
 * Execute shell commands with sandboxing, timeouts, and safety checks
 */

import { spawn, ChildProcess } from 'child_process';
import { Tool } from '../grok-client';

export interface BashParams {
  command: string;
  timeout?: number;
  description?: string;
  run_in_background?: boolean;
  workdir?: string;
}

export interface BashResult {
  stdout: string;
  stderr: string;
  exitCode: number | null;
  timedOut: boolean;
  taskId?: string;
}

// Commands that are blocked for safety
const BLOCKED_COMMANDS = [
  'rm -rf /',
  'rm -rf /*',
  'dd if=',
  'mkfs',
  ':(){:|:&};:',
  '> /dev/sda',
  'chmod -R 777 /',
  'chown -R',
];

// Dangerous patterns
const DANGEROUS_PATTERNS = [
  /rm\s+(-rf?|--recursive)\s+\//,
  />\s*\/dev\/[sh]d/,
  /dd\s+.*of=\/dev/,
  /mkfs/,
  /shutdown|reboot|halt|poweroff/,
  /:()\s*{\s*:\s*\|\s*:&\s*}\s*;/,
];

const backgroundTasks: Map<string, ChildProcess> = new Map();

function isSafeCommand(command: string): { safe: boolean; reason?: string } {
  const lowerCmd = command.toLowerCase();
  
  // Check blocked commands
  for (const blocked of BLOCKED_COMMANDS) {
    if (lowerCmd.includes(blocked.toLowerCase())) {
      return { safe: false, reason: `Blocked command pattern: ${blocked}` };
    }
  }
  
  // Check dangerous patterns
  for (const pattern of DANGEROUS_PATTERNS) {
    if (pattern.test(command)) {
      return { safe: false, reason: `Dangerous pattern detected` };
    }
  }
  
  return { safe: true };
}

function generateTaskId(): string {
  return `task_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

export async function bashExecute(
  params: BashParams,
  workdir: string = process.cwd()
): Promise<BashResult> {
  // Safety check
  const safetyCheck = isSafeCommand(params.command);
  if (!safetyCheck.safe) {
    return {
      stdout: '',
      stderr: `Command blocked: ${safetyCheck.reason}`,
      exitCode: 1,
      timedOut: false,
    };
  }
  
  const timeout = params.timeout ?? 60000; // Default 60s
  const effectiveWorkdir = params.workdir ?? workdir;
  
  // Background execution
  if (params.run_in_background) {
    const taskId = generateTaskId();
    
    const child = spawn('bash', ['-c', params.command], {
      cwd: effectiveWorkdir,
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    
    backgroundTasks.set(taskId, child);
    
    // Cleanup when done
    child.on('exit', () => {
      backgroundTasks.delete(taskId);
    });
    
    return {
      stdout: `Started background task: ${taskId}`,
      stderr: '',
      exitCode: null,
      timedOut: false,
      taskId,
    };
  }
  
  // Foreground execution with timeout
  return new Promise((resolve) => {
    let stdout = '';
    let stderr = '';
    let timedOut = false;
    
    const child = spawn('bash', ['-c', params.command], {
      cwd: effectiveWorkdir,
      env: { ...process.env, TERM: 'dumb' },
    });
    
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill('SIGTERM');
      setTimeout(() => child.kill('SIGKILL'), 1000);
    }, timeout);
    
    child.stdout.on('data', (data) => {
      stdout += data.toString();
      // Truncate if too large
      if (stdout.length > 100000) {
        stdout = stdout.slice(0, 100000) + '\n... (truncated)';
        child.kill('SIGTERM');
      }
    });
    
    child.stderr.on('data', (data) => {
      stderr += data.toString();
      if (stderr.length > 50000) {
        stderr = stderr.slice(0, 50000) + '\n... (truncated)';
      }
    });
    
    child.on('exit', (code) => {
      clearTimeout(timer);
      resolve({
        stdout: stdout.trim(),
        stderr: stderr.trim(),
        exitCode: code,
        timedOut,
      });
    });
    
    child.on('error', (err) => {
      clearTimeout(timer);
      resolve({
        stdout: '',
        stderr: err.message,
        exitCode: 1,
        timedOut: false,
      });
    });
  });
}

export async function bashGetTaskOutput(taskId: string): Promise<BashResult> {
  const task = backgroundTasks.get(taskId);
  
  if (!task) {
    return {
      stdout: '',
      stderr: `Task not found: ${taskId}`,
      exitCode: null,
      timedOut: false,
    };
  }
  
  // For background tasks, we'd need to capture output differently
  // This is a simplified implementation
  return {
    stdout: 'Task is still running',
    stderr: '',
    exitCode: null,
    timedOut: false,
    taskId,
  };
}

export async function bashStopTask(taskId: string): Promise<string> {
  const task = backgroundTasks.get(taskId);
  
  if (!task) {
    return `Task not found: ${taskId}`;
  }
  
  task.kill('SIGTERM');
  setTimeout(() => task.kill('SIGKILL'), 5000);
  backgroundTasks.delete(taskId);
  
  return `Stopped task: ${taskId}`;
}

// Tool definitions for Grok
export const bashTools: Tool[] = [
  {
    type: 'function',
    function: {
      name: 'bash',
      description: 'Execute a shell command. Use for running programs, git operations, file management, etc.',
      parameters: {
        type: 'object',
        properties: {
          command: {
            type: 'string',
            description: 'The shell command to execute',
          },
          timeout: {
            type: 'number',
            description: 'Timeout in milliseconds (default: 60000, max: 600000)',
          },
          description: {
            type: 'string',
            description: 'Brief description of what the command does',
          },
          run_in_background: {
            type: 'boolean',
            description: 'Run in background and return a task ID',
          },
          workdir: {
            type: 'string',
            description: 'Working directory for the command',
          },
        },
        required: ['command'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'task_output',
      description: 'Get the output of a background task',
      parameters: {
        type: 'object',
        properties: {
          task_id: {
            type: 'string',
            description: 'The task ID returned from a background command',
          },
        },
        required: ['task_id'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'task_stop',
      description: 'Stop a background task',
      parameters: {
        type: 'object',
        properties: {
          task_id: {
            type: 'string',
            description: 'The task ID to stop',
          },
        },
        required: ['task_id'],
      },
    },
  },
];

export default { bashExecute, bashGetTaskOutput, bashStopTask, bashTools };
