/**
 * Grok Code - Search Tools
 * 
 * Implements grep, glob, and web search functionality
 */

import { spawn } from 'child_process';
import { glob as globLib } from 'glob';
import { Tool } from '../grok-client';

export interface GrepParams {
  pattern: string;
  path?: string;
  glob?: string;
  output_mode?: 'content' | 'files_with_matches' | 'count';
  context?: number;
  case_insensitive?: boolean;
  head_limit?: number;
}

export interface GlobParams {
  pattern: string;
  path?: string;
}

export interface WebSearchParams {
  query: string;
  allowed_domains?: string[];
  blocked_domains?: string[];
}

/**
 * Search file contents using ripgrep
 */
export async function grep(
  params: GrepParams,
  workdir: string = process.cwd()
): Promise<string> {
  const args: string[] = [];
  
  // Output mode
  if (params.output_mode === 'files_with_matches') {
    args.push('-l');
  } else if (params.output_mode === 'count') {
    args.push('-c');
  }
  
  // Context lines
  if (params.context && params.output_mode === 'content') {
    args.push('-C', params.context.toString());
  }
  
  // Case insensitive
  if (params.case_insensitive) {
    args.push('-i');
  }
  
  // Line numbers
  if (params.output_mode === 'content') {
    args.push('-n');
  }
  
  // Glob filter
  if (params.glob) {
    args.push('--glob', params.glob);
  }
  
  // Pattern
  args.push(params.pattern);
  
  // Path
  args.push(params.path || '.');
  
  return new Promise((resolve, reject) => {
    const child = spawn('rg', args, {
      cwd: workdir,
      env: { ...process.env },
    });
    
    let stdout = '';
    let stderr = '';
    
    child.stdout.on('data', (data) => {
      stdout += data.toString();
      // Limit output
      if (stdout.length > 50000) {
        stdout = stdout.slice(0, 50000) + '\n... (truncated)';
        child.kill();
      }
    });
    
    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    child.on('exit', (code) => {
      if (code === 0 || code === 1) {
        // Code 1 means no matches, which is fine
        let result = stdout.trim();
        
        // Apply head limit
        if (params.head_limit && params.head_limit > 0) {
          const lines = result.split('\n');
          result = lines.slice(0, params.head_limit).join('\n');
        }
        
        resolve(result || 'No matches found');
      } else {
        reject(new Error(stderr || `grep exited with code ${code}`));
      }
    });
    
    child.on('error', (err) => {
      // Fall back to grep if rg not available
      if (err.message.includes('ENOENT')) {
        resolve(grepFallback(params, workdir));
      } else {
        reject(err);
      }
    });
  });
}

/**
 * Fallback to standard grep if ripgrep unavailable
 */
async function grepFallback(params: GrepParams, workdir: string): Promise<string> {
  const args: string[] = ['-r'];
  
  if (params.case_insensitive) args.push('-i');
  if (params.output_mode === 'files_with_matches') args.push('-l');
  if (params.output_mode === 'count') args.push('-c');
  if (params.output_mode === 'content') args.push('-n');
  if (params.context) args.push('-C', params.context.toString());
  
  args.push(params.pattern);
  args.push(params.path || '.');
  
  return new Promise((resolve) => {
    const child = spawn('grep', args, { cwd: workdir });
    let stdout = '';
    
    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    child.on('exit', () => {
      resolve(stdout.trim() || 'No matches found');
    });
  });
}

/**
 * Find files matching a glob pattern
 */
export async function globSearch(
  params: GlobParams,
  workdir: string = process.cwd()
): Promise<string> {
  const searchPath = params.path || workdir;
  
  try {
    const matches = await globLib(params.pattern, {
      cwd: searchPath,
      nodir: false,
      ignore: ['**/node_modules/**', '**/.git/**'],
    });
    
    if (matches.length === 0) {
      return 'No files found matching pattern';
    }
    
    // Limit results
    const limited = matches.slice(0, 100);
    const result = limited.join('\n');
    
    if (matches.length > 100) {
      return result + `\n... and ${matches.length - 100} more files`;
    }
    
    return result;
  } catch (error: any) {
    throw new Error(`Glob search failed: ${error.message}`);
  }
}

/**
 * Web search using configured search API
 */
export async function webSearch(
  params: WebSearchParams,
  apiKey?: string
): Promise<string> {
  // Try Brave Search API
  if (apiKey) {
    try {
      const response = await fetch(
        `https://api.search.brave.com/res/v1/web/search?q=${encodeURIComponent(params.query)}&count=5`,
        {
          headers: {
            'X-Subscription-Token': apiKey,
          },
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        const results = data.web?.results || [];
        
        let filtered = results;
        
        // Apply domain filters
        if (params.allowed_domains?.length) {
          filtered = filtered.filter((r: any) =>
            params.allowed_domains!.some(d => r.url.includes(d))
          );
        }
        if (params.blocked_domains?.length) {
          filtered = filtered.filter((r: any) =>
            !params.blocked_domains!.some(d => r.url.includes(d))
          );
        }
        
        return filtered
          .map((r: any) => `• ${r.title}\n  ${r.url}\n  ${r.description}`)
          .join('\n\n') || 'No results found';
      }
    } catch {
      // Fall through to fallback
    }
  }
  
  // Fallback: return a message about needing an API key
  return `Web search for "${params.query}" requires a Brave Search API key. Please configure one to enable this feature.`;
}

/**
 * Fetch and process a URL
 */
export async function webFetch(
  url: string,
  prompt?: string
): Promise<string> {
  try {
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'GrokCode/1.0',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const contentType = response.headers.get('content-type') || '';
    
    if (contentType.includes('text/html')) {
      const html = await response.text();
      // Basic HTML to text conversion
      const text = html
        .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
        .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
        .replace(/<[^>]+>/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .slice(0, 10000);
      
      return text;
    } else if (contentType.includes('application/json')) {
      const json = await response.json();
      return JSON.stringify(json, null, 2).slice(0, 10000);
    } else {
      const text = await response.text();
      return text.slice(0, 10000);
    }
  } catch (error: any) {
    throw new Error(`Failed to fetch URL: ${error.message}`);
  }
}

// Tool definitions for Grok
export const searchTools: Tool[] = [
  {
    type: 'function',
    function: {
      name: 'grep',
      description: 'Search file contents using regex patterns. Uses ripgrep for fast searching.',
      parameters: {
        type: 'object',
        properties: {
          pattern: {
            type: 'string',
            description: 'Regular expression pattern to search for',
          },
          path: {
            type: 'string',
            description: 'Directory or file to search in (default: current directory)',
          },
          glob: {
            type: 'string',
            description: 'File pattern to filter (e.g., "*.ts", "*.{js,jsx}")',
          },
          output_mode: {
            type: 'string',
            enum: ['content', 'files_with_matches', 'count'],
            description: 'Output format (default: files_with_matches)',
          },
          context: {
            type: 'number',
            description: 'Lines of context around matches',
          },
          case_insensitive: {
            type: 'boolean',
            description: 'Case insensitive search',
          },
          head_limit: {
            type: 'number',
            description: 'Limit output to first N results',
          },
        },
        required: ['pattern'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'glob',
      description: 'Find files matching a glob pattern',
      parameters: {
        type: 'object',
        properties: {
          pattern: {
            type: 'string',
            description: 'Glob pattern (e.g., "**/*.ts", "src/**/*.js")',
          },
          path: {
            type: 'string',
            description: 'Base directory to search from',
          },
        },
        required: ['pattern'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'web_search',
      description: 'Search the web for information',
      parameters: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: 'Search query',
          },
          allowed_domains: {
            type: 'array',
            items: { type: 'string' },
            description: 'Only include results from these domains',
          },
          blocked_domains: {
            type: 'array',
            items: { type: 'string' },
            description: 'Exclude results from these domains',
          },
        },
        required: ['query'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'web_fetch',
      description: 'Fetch and extract content from a URL',
      parameters: {
        type: 'object',
        properties: {
          url: {
            type: 'string',
            description: 'The URL to fetch',
          },
          prompt: {
            type: 'string',
            description: 'Optional prompt to process the content',
          },
        },
        required: ['url'],
      },
    },
  },
];

export default { grep, globSearch, webSearch, webFetch, searchTools };
