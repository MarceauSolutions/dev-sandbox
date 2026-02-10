const ChatPage = {
  title: 'AI Assistant',
  _history: [],

  async init() {
    this._history = [];
  },

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>AI Assistant</h1>
        <p>Your fitness content co-pilot</p>
      </div>

      <div class="card" style="display:flex;flex-direction:column;height:calc(100vh - 220px);min-height:400px">
        <div class="card-header">
          <span class="card-title">Chat</span>
          <button class="btn btn-sm btn-ghost" id="chat-clear-btn">Clear Chat</button>
        </div>

        <div class="chat-container" style="flex:1;display:flex;flex-direction:column;overflow:hidden">
          <div class="chat-messages" id="chat-messages" style="flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px">
            <div class="chat-msg assistant">
              <div class="chat-bubble">Hey! I'm your fitness content assistant. Ask me about workout plans, nutrition, content ideas, captions, hooks, or anything else!</div>
            </div>
          </div>

          <div class="quick-prompts" style="padding:8px 16px;display:flex;gap:8px;flex-wrap:wrap;border-top:1px solid var(--border)">
            <button class="tag quick-prompt-btn">Workout Plan</button>
            <button class="tag quick-prompt-btn">Nutrition Guide</button>
            <button class="tag quick-prompt-btn">Content Ideas</button>
            <button class="tag quick-prompt-btn">Caption Help</button>
            <button class="tag quick-prompt-btn">Hook Ideas</button>
          </div>

          <div class="chat-input-area" style="padding:12px 16px;border-top:1px solid var(--border);display:flex;gap:8px">
            <input type="text" id="chat-input" class="form-input" placeholder="Ask me anything about fitness content..." style="flex:1" autocomplete="off">
            <button class="btn btn-primary" id="chat-send-btn">Send</button>
          </div>
        </div>
      </div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    const input = container.querySelector('#chat-input');
    const sendBtn = container.querySelector('#chat-send-btn');
    const clearBtn = container.querySelector('#chat-clear-btn');
    const messagesEl = container.querySelector('#chat-messages');

    const sendMessage = async () => {
      const text = input.value.trim();
      if (!text) return;

      // Append user message to UI
      this._appendMessage(messagesEl, 'user', text);
      input.value = '';

      // Add to history
      this._history.push({ role: 'user', content: text });

      // Show typing indicator
      const typingEl = document.createElement('div');
      typingEl.className = 'chat-msg assistant';
      typingEl.id = 'chat-typing';
      typingEl.innerHTML = '<div class="chat-bubble"><div class="spinner" style="width:16px;height:16px;display:inline-block"></div> Thinking...</div>';
      messagesEl.appendChild(typingEl);
      messagesEl.scrollTop = messagesEl.scrollHeight;

      // Disable input while processing
      input.disabled = true;
      sendBtn.disabled = true;

      try {
        const res = await API.post('/api/ai/chat', {
          message: text,
          conversation_history: this._history.slice(0, -1)
        });

        // Remove typing indicator
        const typing = messagesEl.querySelector('#chat-typing');
        if (typing) typing.remove();

        const reply = res.response || res.message || res.content || 'No response received.';
        this._appendMessage(messagesEl, 'assistant', reply);
        this._history.push({ role: 'assistant', content: reply });
      } catch (err) {
        const typing = messagesEl.querySelector('#chat-typing');
        if (typing) typing.remove();
        this._appendMessage(messagesEl, 'assistant', 'Sorry, something went wrong: ' + err.message);
      } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
      }
    };

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    clearBtn.addEventListener('click', () => {
      this._history = [];
      messagesEl.innerHTML = `
        <div class="chat-msg assistant">
          <div class="chat-bubble">Chat cleared! How can I help you?</div>
        </div>
      `;
    });

    // Quick prompt buttons
    container.querySelectorAll('.quick-prompt-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        input.value = btn.textContent;
        sendMessage();
      });
    });

    input.focus();
  },

  _appendMessage(messagesEl, role, content) {
    const msgEl = document.createElement('div');
    msgEl.className = `chat-msg ${role}`;

    // Convert newlines to <br> and preserve basic formatting
    const formatted = content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>');

    msgEl.innerHTML = `<div class="chat-bubble">${formatted}</div>`;
    messagesEl.appendChild(msgEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  },

  destroy() {
    this._history = [];
  }
};
