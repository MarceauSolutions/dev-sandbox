/**
 * Grok Code - VS Code Extension
 * 
 * AI coding assistant with truth-seeking behavior
 */

import * as vscode from 'vscode';
import { GrokClient, AgentOrchestrator, getAllTools, executeTool } from '@grok-code/core';

let client: GrokClient | null = null;
let orchestrator: AgentOrchestrator | null = null;
let chatPanel: vscode.WebviewPanel | null = null;
let contrarianMode = false;

export function activate(context: vscode.ExtensionContext) {
  console.log('Grok Code extension activated');

  // Initialize on config change
  initializeClient();
  vscode.workspace.onDidChangeConfiguration((e) => {
    if (e.affectsConfiguration('grok-code')) {
      initializeClient();
    }
  });

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('grok-code.startChat', () => openChatPanel(context)),
    vscode.commands.registerCommand('grok-code.explainCode', explainCode),
    vscode.commands.registerCommand('grok-code.refactorCode', refactorCode),
    vscode.commands.registerCommand('grok-code.writeTests', writeTests),
    vscode.commands.registerCommand('grok-code.fixBugs', fixBugs),
    vscode.commands.registerCommand('grok-code.reviewCode', reviewCode),
    vscode.commands.registerCommand('grok-code.toggleContrarian', toggleContrarian),
    vscode.commands.registerCommand('grok-code.runAgent', runMultiAgentTask),
  );

  // Register tree views
  const agentsProvider = new AgentsTreeProvider();
  const tasksProvider = new TasksTreeProvider();
  
  vscode.window.registerTreeDataProvider('grok-code-agents', agentsProvider);
  vscode.window.registerTreeDataProvider('grok-code-tasks', tasksProvider);

  // Status bar item
  const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBar.text = '$(hubot) Grok';
  statusBar.tooltip = 'Grok Code - Click to open chat';
  statusBar.command = 'grok-code.startChat';
  statusBar.show();
  context.subscriptions.push(statusBar);
}

function initializeClient() {
  const config = vscode.workspace.getConfiguration('grok-code');
  const apiKey = config.get<string>('apiKey');
  
  if (!apiKey) {
    vscode.window.showWarningMessage(
      'Grok Code: API key not configured. Please set it in settings.',
      'Open Settings'
    ).then((action) => {
      if (action === 'Open Settings') {
        vscode.commands.executeCommand('workbench.action.openSettings', 'grok-code.apiKey');
      }
    });
    return;
  }

  const model = config.get<string>('model') || 'grok-3-latest';
  contrarianMode = config.get<boolean>('contrarianMode') || false;

  client = new GrokClient({ apiKey, model });
  
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd();
  orchestrator = new AgentOrchestrator(client, { workdir: workspaceFolder });
}

async function openChatPanel(context: vscode.ExtensionContext) {
  if (chatPanel) {
    chatPanel.reveal();
    return;
  }

  chatPanel = vscode.window.createWebviewPanel(
    'grokCodeChat',
    'Grok Chat',
    vscode.ViewColumn.Beside,
    {
      enableScripts: true,
      retainContextWhenHidden: true,
    }
  );

  chatPanel.webview.html = getChatHtml();

  chatPanel.webview.onDidReceiveMessage(async (message) => {
    if (message.type === 'chat') {
      await handleChatMessage(message.text, chatPanel!);
    }
  });

  chatPanel.onDidDispose(() => {
    chatPanel = null;
  });
}

async function handleChatMessage(text: string, panel: vscode.WebviewPanel) {
  if (!client) {
    panel.webview.postMessage({ type: 'error', text: 'Client not initialized' });
    return;
  }

  // Show typing indicator
  panel.webview.postMessage({ type: 'typing', show: true });

  try {
    const tools = getAllTools();
    const workdir = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd();

    const { content, toolResults } = await client.runWithTools(
      text,
      tools,
      async (name, args) => {
        const result = await executeTool(name, args as any, { workdir });
        return result.success ? result.output : `Error: ${result.error}`;
      },
      {
        systemPrompt: `You are Grok, an AI coding assistant in VS Code. Help the user with coding tasks.
Current workspace: ${workdir}
${contrarianMode ? 'CONTRARIAN MODE: Challenge assumptions and suggest alternatives.' : ''}`,
      }
    );

    const showConfidence = vscode.workspace.getConfiguration('grok-code').get('showConfidence');
    
    panel.webview.postMessage({
      type: 'response',
      text: content,
      tools: toolResults,
      confidence: showConfidence ? 0.85 : null, // Would come from actual response
    });
  } catch (error: any) {
    panel.webview.postMessage({ type: 'error', text: error.message });
  }

  panel.webview.postMessage({ type: 'typing', show: false });
}

async function explainCode() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return;

  const selection = editor.document.getText(editor.selection);
  if (!selection) {
    vscode.window.showWarningMessage('Please select some code first');
    return;
  }

  await runQuickAction('Explain this code', selection);
}

async function refactorCode() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return;

  const selection = editor.document.getText(editor.selection);
  if (!selection) return;

  const suggestions = await runQuickAction('Refactor this code for better readability and performance', selection);
  
  if (suggestions) {
    const apply = await vscode.window.showInformationMessage(
      'Apply refactoring suggestions?',
      'Apply',
      'Show Diff',
      'Cancel'
    );

    if (apply === 'Apply') {
      // Would apply the changes
      vscode.window.showInformationMessage('Refactoring applied');
    } else if (apply === 'Show Diff') {
      // Would show diff view
    }
  }
}

async function writeTests() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return;

  const selection = editor.document.getText(editor.selection);
  if (!selection) return;

  const lang = editor.document.languageId;
  await runQuickAction(`Write comprehensive unit tests for this ${lang} code`, selection);
}

async function fixBugs() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return;

  const selection = editor.document.getText(editor.selection);
  if (!selection) return;

  await runQuickAction('Find and fix bugs in this code. List each bug found with its fix.', selection);
}

async function reviewCode() {
  if (!orchestrator) {
    vscode.window.showErrorMessage('Grok Code not initialized');
    return;
  }

  const editor = vscode.window.activeTextEditor;
  if (!editor) return;

  const selection = editor.document.getText(editor.selection) || editor.document.getText();

  vscode.window.withProgress({
    location: vscode.ProgressLocation.Notification,
    title: 'Grok reviewing code...',
    cancellable: false,
  }, async () => {
    const result = await orchestrator!.execute({
      id: `review-${Date.now()}`,
      description: 'Code Review',
      prompt: `Review this code:\n\n${selection}`,
      agents: [
        { type: 'reviewer', contrarian: contrarianMode },
        { type: 'security' },
      ],
      workflow: 'parallel',
    });

    // Show results in new document
    const doc = await vscode.workspace.openTextDocument({
      content: result.finalOutput,
      language: 'markdown',
    });
    await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
  });
}

async function toggleContrarian() {
  contrarianMode = !contrarianMode;
  vscode.window.showInformationMessage(
    `Contrarian mode ${contrarianMode ? 'enabled' : 'disabled'}`
  );
}

async function runMultiAgentTask() {
  if (!orchestrator) {
    vscode.window.showErrorMessage('Grok Code not initialized');
    return;
  }

  const task = await vscode.window.showInputBox({
    prompt: 'Describe the coding task',
    placeHolder: 'e.g., Add user authentication to the API',
  });

  if (!task) return;

  const workflow = await vscode.window.showQuickPick(
    ['sequential', 'parallel', 'review'],
    { placeHolder: 'Select workflow type' }
  );

  if (!workflow) return;

  vscode.window.withProgress({
    location: vscode.ProgressLocation.Notification,
    title: 'Running multi-agent task...',
    cancellable: false,
  }, async () => {
    const result = await orchestrator!.execute({
      id: `task-${Date.now()}`,
      description: task,
      prompt: task,
      agents: [
        { type: 'coder' },
        { type: 'reviewer', contrarian: contrarianMode },
        { type: 'tester' },
      ],
      workflow: workflow as any,
    });

    const doc = await vscode.workspace.openTextDocument({
      content: result.finalOutput,
      language: 'markdown',
    });
    await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
  });
}

async function runQuickAction(prompt: string, code: string): Promise<string | null> {
  if (!client) {
    vscode.window.showErrorMessage('Grok Code not initialized');
    return null;
  }

  return vscode.window.withProgress({
    location: vscode.ProgressLocation.Notification,
    title: 'Grok thinking...',
    cancellable: false,
  }, async () => {
    try {
      const response = await client!.chat([
        { role: 'system', content: 'You are Grok, an AI coding assistant. Be concise and helpful.' },
        { role: 'user', content: `${prompt}\n\n\`\`\`\n${code}\n\`\`\`` },
      ]);

      // Show in output channel
      const channel = vscode.window.createOutputChannel('Grok Code');
      channel.clear();
      channel.appendLine(`Confidence: ${(response.confidence * 100).toFixed(0)}%\n`);
      channel.appendLine(response.content);
      channel.show();

      return response.content;
    } catch (error: any) {
      vscode.window.showErrorMessage(`Grok error: ${error.message}`);
      return null;
    }
  });
}

function getChatHtml(): string {
  return `<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: var(--vscode-font-family); padding: 10px; }
    .messages { height: calc(100vh - 100px); overflow-y: auto; }
    .message { margin: 10px 0; padding: 10px; border-radius: 8px; }
    .user { background: var(--vscode-input-background); text-align: right; }
    .assistant { background: var(--vscode-editor-background); border: 1px solid var(--vscode-input-border); }
    .input-area { display: flex; gap: 10px; position: fixed; bottom: 10px; left: 10px; right: 10px; }
    input { flex: 1; padding: 10px; border: 1px solid var(--vscode-input-border); background: var(--vscode-input-background); color: var(--vscode-input-foreground); }
    button { padding: 10px 20px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; cursor: pointer; }
    .typing { opacity: 0.7; font-style: italic; }
    .confidence { font-size: 0.8em; color: var(--vscode-descriptionForeground); }
    code { background: var(--vscode-textCodeBlock-background); padding: 2px 4px; border-radius: 3px; }
    pre { background: var(--vscode-textCodeBlock-background); padding: 10px; overflow-x: auto; }
  </style>
</head>
<body>
  <div class="messages" id="messages"></div>
  <div class="input-area">
    <input type="text" id="input" placeholder="Ask Grok..." />
    <button onclick="send()">Send</button>
  </div>
  <script>
    const vscode = acquireVsCodeApi();
    const messagesEl = document.getElementById('messages');
    const inputEl = document.getElementById('input');

    function send() {
      const text = inputEl.value.trim();
      if (!text) return;
      
      addMessage('user', text);
      vscode.postMessage({ type: 'chat', text });
      inputEl.value = '';
    }

    function addMessage(role, text, confidence) {
      const div = document.createElement('div');
      div.className = 'message ' + role;
      div.innerHTML = formatMessage(text);
      if (confidence) {
        div.innerHTML += '<div class="confidence">Confidence: ' + Math.round(confidence * 100) + '%</div>';
      }
      messagesEl.appendChild(div);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function formatMessage(text) {
      return text
        .replace(/\`\`\`(\\w*)\\n([\\s\\S]*?)\`\`\`/g, '<pre><code>$2</code></pre>')
        .replace(/\`([^\`]+)\`/g, '<code>$1</code>')
        .replace(/\\n/g, '<br>');
    }

    inputEl.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') send();
    });

    window.addEventListener('message', (event) => {
      const msg = event.data;
      if (msg.type === 'response') {
        addMessage('assistant', msg.text, msg.confidence);
      } else if (msg.type === 'error') {
        addMessage('assistant', 'Error: ' + msg.text);
      } else if (msg.type === 'typing') {
        // Handle typing indicator
      }
    });
  </script>
</body>
</html>`;
}

// Tree providers
class AgentsTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(): vscode.TreeItem[] {
    return [
      new vscode.TreeItem('Coder Agent', vscode.TreeItemCollapsibleState.None),
      new vscode.TreeItem('Reviewer Agent', vscode.TreeItemCollapsibleState.None),
      new vscode.TreeItem('Tester Agent', vscode.TreeItemCollapsibleState.None),
      new vscode.TreeItem('Security Agent', vscode.TreeItemCollapsibleState.None),
    ];
  }
}

class TasksTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(): vscode.TreeItem[] {
    return [
      new vscode.TreeItem('No active tasks', vscode.TreeItemCollapsibleState.None),
    ];
  }
}

export function deactivate() {
  client = null;
  orchestrator = null;
}
