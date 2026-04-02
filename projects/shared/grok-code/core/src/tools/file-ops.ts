/**
 * Grok Code - File Operation Tools
 * 
 * Implements FileRead, FileWrite, FileEdit with safety checks
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { Tool } from '../grok-client';

export interface FileReadParams {
  file_path: string;
  offset?: number;
  limit?: number;
}

export interface FileWriteParams {
  file_path: string;
  content: string;
}

export interface FileEditParams {
  file_path: string;
  old_string: string;
  new_string: string;
  replace_all?: boolean;
}

// Protected paths that should never be modified
const PROTECTED_PATHS = [
  '/home/clawdbot/app',
  '/home/clawdbot/clawd',
  '/etc',
  '/usr',
  '/bin',
  '/sbin',
  '/var',
  '/root',
];

function isProtectedPath(filePath: string): boolean {
  const resolved = path.resolve(filePath);
  return PROTECTED_PATHS.some(p => resolved.startsWith(p));
}

function ensureAbsolutePath(filePath: string, workdir: string): string {
  if (path.isAbsolute(filePath)) {
    return filePath;
  }
  return path.join(workdir, filePath);
}

export async function fileRead(
  params: FileReadParams,
  workdir: string = process.cwd()
): Promise<string> {
  const filePath = ensureAbsolutePath(params.file_path, workdir);
  
  try {
    const content = await fs.readFile(filePath, 'utf-8');
    const lines = content.split('\n');
    
    const offset = params.offset ?? 0;
    const limit = params.limit ?? lines.length;
    
    const selectedLines = lines.slice(offset, offset + limit);
    
    return selectedLines.join('\n');
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      throw new Error(`File not found: ${filePath}`);
    }
    throw error;
  }
}

export async function fileWrite(
  params: FileWriteParams,
  workdir: string = process.cwd()
): Promise<string> {
  const filePath = ensureAbsolutePath(params.file_path, workdir);
  
  if (isProtectedPath(filePath)) {
    throw new Error(`Cannot write to protected path: ${filePath}`);
  }
  
  // Create directory if needed
  const dir = path.dirname(filePath);
  await fs.mkdir(dir, { recursive: true });
  
  await fs.writeFile(filePath, params.content, 'utf-8');
  
  return `Successfully wrote ${params.content.length} bytes to ${filePath}`;
}

export async function fileEdit(
  params: FileEditParams,
  workdir: string = process.cwd()
): Promise<string> {
  const filePath = ensureAbsolutePath(params.file_path, workdir);
  
  if (isProtectedPath(filePath)) {
    throw new Error(`Cannot edit protected path: ${filePath}`);
  }
  
  const content = await fs.readFile(filePath, 'utf-8');
  
  if (!content.includes(params.old_string)) {
    throw new Error(`String not found in file: "${params.old_string.slice(0, 50)}..."`);
  }
  
  let newContent: string;
  let count: number;
  
  if (params.replace_all) {
    const parts = content.split(params.old_string);
    count = parts.length - 1;
    newContent = parts.join(params.new_string);
  } else {
    newContent = content.replace(params.old_string, params.new_string);
    count = 1;
  }
  
  await fs.writeFile(filePath, newContent, 'utf-8');
  
  return `Successfully edited ${filePath} (${count} replacement${count > 1 ? 's' : ''})`;
}

// Tool definitions for Grok
export const fileTools: Tool[] = [
  {
    type: 'function',
    function: {
      name: 'file_read',
      description: 'Read the contents of a file. Supports pagination with offset/limit for large files.',
      parameters: {
        type: 'object',
        properties: {
          file_path: {
            type: 'string',
            description: 'The path to the file to read (absolute or relative)',
          },
          offset: {
            type: 'number',
            description: 'Line number to start reading from (0-indexed)',
          },
          limit: {
            type: 'number',
            description: 'Maximum number of lines to read',
          },
        },
        required: ['file_path'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'file_write',
      description: 'Write content to a file. Creates parent directories if needed. Overwrites existing files.',
      parameters: {
        type: 'object',
        properties: {
          file_path: {
            type: 'string',
            description: 'The path to the file to write (absolute or relative)',
          },
          content: {
            type: 'string',
            description: 'The content to write to the file',
          },
        },
        required: ['file_path', 'content'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'file_edit',
      description: 'Edit a file by replacing text. The old_string must match exactly.',
      parameters: {
        type: 'object',
        properties: {
          file_path: {
            type: 'string',
            description: 'The path to the file to edit',
          },
          old_string: {
            type: 'string',
            description: 'The exact text to find and replace',
          },
          new_string: {
            type: 'string',
            description: 'The text to replace it with',
          },
          replace_all: {
            type: 'boolean',
            description: 'Replace all occurrences (default: false)',
          },
        },
        required: ['file_path', 'old_string', 'new_string'],
      },
    },
  },
];

export default { fileRead, fileWrite, fileEdit, fileTools };
