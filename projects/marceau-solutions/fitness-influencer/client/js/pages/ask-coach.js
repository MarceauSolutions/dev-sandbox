/* ============================================================
   Ask Coach Page — Client Portal
   AI chat interface with conversation history
   ============================================================ */

const AskCoachPage = {
  title: 'Ask Coach',
  messages: [],
  isLoading: false,

  init() {
    // Conversation persists for the session
    if (!this.messages.length) {
      this.messages = [{
        role: 'assistant',
        content: "Hey! I'm your AI coach assistant. Ask me anything about your workouts, nutrition, recovery, or progress. How can I help today?"
      }];
    }
  },

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>Ask Coach</h1>
        <p>Get instant guidance on training, nutrition, and recovery</p>
      </div>

      <div class="card" style="padding:0;overflow:hidden">
        <div class="chat-container">
          <!-- Quick Prompts -->
          <div class="quick-prompts" style="padding:14px 18px 0" id="coach-prompts">
            <button class="quick-prompt-chip" onclick="AskCoachPage.sendQuickPrompt('What is my workout today?')">My Workout Today</button>
            <button class="quick-prompt-chip" onclick="AskCoachPage.sendQuickPrompt('I have a nutrition question about my macros.')">Nutrition Question</button>
            <button class="quick-prompt-chip" onclick="AskCoachPage.sendQuickPrompt('I need help with recovery. My muscles are sore.')">Recovery Help</button>
            <button class="quick-prompt-chip" onclick="AskCoachPage.sendQuickPrompt('How is my progress looking this week?')">Check My Progress</button>
          </div>

          <!-- Messages -->
          <div class="chat-messages" id="coach-messages" style="padding:18px">
            ${this._renderMessages()}
          </div>

          <!-- Input -->
          <div class="chat-input-area" style="padding:14px 18px 18px">
            <textarea class="chat-input" id="coach-input" placeholder="Ask your coach anything..."
              rows="1" onkeydown="AskCoachPage.handleKeyDown(event)"></textarea>
            <button class="btn btn-primary" id="coach-send" onclick="AskCoachPage.sendMessage()" style="min-width:80px">
              Send
            </button>
          </div>
        </div>
      </div>
    `;

    // Scroll to bottom
    this._scrollToBottom();

    // Auto-resize textarea
    const input = document.getElementById('coach-input');
    if (input) {
      input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
      });
    }
  },

  _renderMessages() {
    return this.messages.map(msg => {
      const isUser = msg.role === 'user';
      return `
        <div class="chat-msg ${isUser ? 'user' : 'assistant'}">
          <div class="chat-avatar">${isUser ? '&#128170;' : '&#127769;'}</div>
          <div class="chat-bubble">${this._formatMessage(msg.content)}</div>
        </div>
      `;
    }).join('');
  },

  _formatMessage(text) {
    if (!text) return '';
    // Basic markdown-like formatting
    let html = this._esc(text);
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    // Bullet points
    html = html.replace(/^- (.*)/gm, '<li style="margin-left:16px;list-style:disc">$1</li>');
    return html;
  },

  handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      this.sendMessage();
    }
  },

  sendQuickPrompt(text) {
    document.getElementById('coach-input').value = text;
    this.sendMessage();
  },

  async sendMessage() {
    const input = document.getElementById('coach-input');
    const text = input.value.trim();
    if (!text || this.isLoading) return;

    // Add user message
    this.messages.push({ role: 'user', content: text });
    input.value = '';
    input.style.height = 'auto';

    // Hide quick prompts after first message
    const prompts = document.getElementById('coach-prompts');
    if (prompts && this.messages.filter(m => m.role === 'user').length >= 1) {
      prompts.style.display = 'none';
    }

    // Re-render messages with user message + loading indicator
    const msgContainer = document.getElementById('coach-messages');
    if (msgContainer) {
      msgContainer.innerHTML = this._renderMessages() + `
        <div class="chat-msg assistant" id="coach-loading">
          <div class="chat-avatar">&#127769;</div>
          <div class="chat-bubble">
            <div class="spinner" style="width:16px;height:16px;display:inline-block;vertical-align:middle"></div>
            <span style="margin-left:8px;color:var(--text-secondary)">Thinking...</span>
          </div>
        </div>
      `;
      this._scrollToBottom();
    }

    // Disable send button
    this.isLoading = true;
    const sendBtn = document.getElementById('coach-send');
    if (sendBtn) sendBtn.disabled = true;

    try {
      const result = await API.post('/api/client/chat', {
        message: text,
        conversation_history: this.messages.slice(-20) // Send last 20 messages for context
      });

      const reply = result.response || result.message || 'I apologize, I could not generate a response. Please try again.';
      this.messages.push({ role: 'assistant', content: reply });
    } catch (err) {
      this.messages.push({
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again in a moment.'
      });
      Toast.error(err.message);
    } finally {
      this.isLoading = false;
      if (sendBtn) sendBtn.disabled = false;
    }

    // Re-render
    if (msgContainer) {
      msgContainer.innerHTML = this._renderMessages();
      this._scrollToBottom();
    }
  },

  _scrollToBottom() {
    const msgContainer = document.getElementById('coach-messages');
    if (msgContainer) {
      setTimeout(() => {
        msgContainer.scrollTop = msgContainer.scrollHeight;
      }, 50);
    }
  },

  _esc(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
};
