(function () {
  'use strict';

  const chatArea = document.getElementById('chat-area');
  const messageInput = document.getElementById('message-input');
  const sendBtn = document.getElementById('send-btn');
  const imageInput = document.getElementById('image-input');
  const imagePreview = document.getElementById('image-preview');
  const profileSelect = document.getElementById('profile-select');
  const usageBtn = document.getElementById('usage-btn');
  const clearBtn = document.getElementById('clear-btn');
  const usageModal = document.getElementById('usage-modal');
  const usageClose = document.getElementById('usage-close');
  const usageBody = document.getElementById('usage-body');
  const welcomeMessage = document.getElementById('welcome-message');

  let pendingImages = [];
  let isStreaming = false;
  let mathjaxTimer = null;

  function getSessionId() {
    let id = localStorage.getItem('qsever_session_id');
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem('qsever_session_id', id);
    }
    return id;
  }

  const sessionId = getSessionId();

  function getHeaders() {
    return { 'X-Session-ID': sessionId };
  }

  function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  function hideWelcome() {
    if (welcomeMessage) {
      welcomeMessage.style.display = 'none';
    }
  }

  function appendUserMessage(text, images) {
    hideWelcome();
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message user';

    let content = '';
    if (images && images.length > 0) {
      content += images.map(img =>
        `<img src="/api/images/file/${img}" style="max-width:120px;max-height:120px;border-radius:8px;margin-right:8px;">`
      ).join('');
    }
    if (text) {
      content += `<span>${escapeHtml(text)}</span>`;
    }

    msgDiv.innerHTML = `<div class="message-bubble">${content}</div>`;
    chatArea.appendChild(msgDiv);
    scrollToBottom();
  }

  function appendAIBubble() {
    hideWelcome();
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ai';
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    msgDiv.appendChild(bubble);
    chatArea.appendChild(msgDiv);
    scrollToBottom();
    return bubble;
  }

  function renderMarkdown(element, text) {
    const LBRACKET = '%%LBRACKET%%';
    const RBRACKET = '%%RBRACKET%%';
    const LPAREN = '%%LPAREN%%';
    const RPAREN = '%%RPAREN%%';

    let protected_text = text
      .replace(/\\\[/g, LBRACKET)
      .replace(/\\\]/g, RBRACKET)
      .replace(/\\\(/g, LPAREN)
      .replace(/\\\)/g, RPAREN);

    let html = marked.parse(protected_text);

    html = html
      .replace(new RegExp(LBRACKET, 'g'), '\\[')
      .replace(new RegExp(RBRACKET, 'g'), '\\]')
      .replace(new RegExp(LPAREN, 'g'), '\\(')
      .replace(new RegExp(RPAREN, 'g'), '\\)');

    element.innerHTML = html;
  }

  function typesetMath(element) {
    if (window.MathJax && MathJax.typesetPromise) {
      MathJax.typesetPromise([element]).catch(() => {});
    }
  }

  function debounceTypeset(element) {
    if (mathjaxTimer) clearTimeout(mathjaxTimer);
    mathjaxTimer = setTimeout(() => {
      typesetMath(element);
    }, 200);
  }

  function showError(bubble, message) {
    bubble.className = 'message-bubble error-bubble';
    bubble.textContent = message;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function parseSSEEvents(buffer) {
    const events = [];
    const parts = buffer.split('\n\n');
    let remaining = '';

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i].trim();
      if (!part) continue;

      if (i === parts.length - 1 && !buffer.endsWith('\n\n')) {
        remaining = part;
        break;
      }

      let eventType = 'message';
      let data = '';

      for (const line of part.split('\n')) {
        if (line.startsWith('event:')) {
          eventType = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
          data = line.slice(5).trim();
        }
      }

      if (data) {
        try {
          events.push({ type: eventType, data: JSON.parse(data) });
        } catch {
          events.push({ type: eventType, data: {} });
        }
      }
    }

    return { parsed: events, remaining };
  }

  async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text && pendingImages.length === 0) return;
    if (isStreaming) return;

    const images = pendingImages.map(img => img.name);
    messageInput.value = '';
    messageInput.style.height = 'auto';
    clearImagePreview();
    isStreaming = true;
    sendBtn.disabled = true;

    appendUserMessage(text, images);
    const bubble = appendAIBubble();

    let fullText = '';
    let buffer = '';

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getHeaders(),
        },
        body: JSON.stringify({ message: text, images }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: '请求失败' }));
        showError(bubble, err.detail || '请求失败');
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const { parsed, remaining } = parseSSEEvents(buffer);
        buffer = remaining;

        for (const event of parsed) {
          if (event.type === 'delta') {
            fullText += event.data.content;
            renderMarkdown(bubble, fullText);
            debounceTypeset(bubble);
            scrollToBottom();
          } else if (event.type === 'usage') {
            // usage info received
          } else if (event.type === 'error') {
            showError(bubble, event.data.message || '发生错误');
          } else if (event.type === 'done') {
            typesetMath(bubble);
          }
        }
      }

      if (fullText) {
        renderMarkdown(bubble, fullText);
        typesetMath(bubble);
      }
    } catch (err) {
      if (!fullText) {
        showError(bubble, '网络错误: ' + err.message);
      }
    } finally {
      isStreaming = false;
      sendBtn.disabled = false;
      messageInput.focus();
    }
  }

  function clearImagePreview() {
    pendingImages = [];
    imagePreview.innerHTML = '';
  }

  async function handleImageUpload(files) {
    for (const file of files) {
      if (!file.type.startsWith('image/')) continue;

      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await fetch('/api/images/upload', {
          method: 'POST',
          headers: getHeaders(),
          body: formData,
        });
        const data = await res.json();
        if (data.ok) {
          pendingImages.push({ name: data.filename, file });
          addImagePreviewItem(data.filename, file);
        }
      } catch (err) {
        console.error('Upload failed:', err);
      }
    }
    imageInput.value = '';
  }

  function addImagePreviewItem(name, file) {
    const item = document.createElement('div');
    item.className = 'image-preview-item';
    item.dataset.name = name;

    const img = document.createElement('img');
    img.src = URL.createObjectURL(file);
    item.appendChild(img);

    const removeBtn = document.createElement('button');
    removeBtn.className = 'remove-image';
    removeBtn.textContent = '×';
    removeBtn.onclick = () => {
      pendingImages = pendingImages.filter(i => i.name !== name);
      item.remove();
    };
    item.appendChild(removeBtn);

    imagePreview.appendChild(item);
  }

  async function loadConfig() {
    try {
      const res = await fetch('/api/config', { headers: getHeaders() });
      const data = await res.json();
      profileSelect.innerHTML = '';
      for (const p of data.profiles) {
        const opt = document.createElement('option');
        opt.value = p.name;
        opt.textContent = `${p.name} (${p.model_id})`;
        if (p.name === data.active_profile) opt.selected = true;
        profileSelect.appendChild(opt);
      }
    } catch (err) {
      console.error('Load config failed:', err);
    }
  }

  async function switchProfile(name) {
    try {
      await fetch('/api/config/active', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...getHeaders() },
        body: JSON.stringify({ profile: name }),
      });
    } catch (err) {
      console.error('Switch profile failed:', err);
    }
  }

  async function showUsage() {
    try {
      const res = await fetch('/api/usage', { headers: getHeaders() });
      const data = await res.json();
      usageBody.innerHTML = `
        <div class="usage-item"><span class="usage-label">请求数</span><span class="usage-value">${data.total_requests}</span></div>
        <div class="usage-item"><span class="usage-label">总 Tokens</span><span class="usage-value">${data.total_tokens.toLocaleString()}</span></div>
        <div class="usage-item"><span class="usage-label">输入 Tokens</span><span class="usage-value">${data.total_prompt_tokens.toLocaleString()}</span></div>
        <div class="usage-item"><span class="usage-label">输出 Tokens</span><span class="usage-value">${data.total_completion_tokens.toLocaleString()}</span></div>
        <div class="usage-item"><span class="usage-label">总费用</span><span class="usage-value">$${data.total_cost.toFixed(4)}</span></div>
        <div class="usage-item"><span class="usage-label">剩余预算</span><span class="usage-value">$${data.remaining_budget.toFixed(4)}</span></div>
      `;
      usageModal.classList.add('active');
    } catch (err) {
      console.error('Load usage failed:', err);
    }
  }

  async function clearConversation() {
    if (!confirm('确定清空对话历史？')) return;
    try {
      await fetch('/api/conversation', { method: 'DELETE', headers: getHeaders() });
      chatArea.innerHTML = '';
      chatArea.appendChild(welcomeMessage);
      welcomeMessage.style.display = '';
    } catch (err) {
      console.error('Clear failed:', err);
    }
  }

  // Event listeners
  sendBtn.addEventListener('click', sendMessage);

  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  messageInput.addEventListener('input', () => {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
  });

  imageInput.addEventListener('change', (e) => {
    handleImageUpload(e.target.files);
  });

  profileSelect.addEventListener('change', (e) => {
    switchProfile(e.target.value);
  });

  usageBtn.addEventListener('click', showUsage);
  clearBtn.addEventListener('click', clearConversation);

  usageClose.addEventListener('click', () => {
    usageModal.classList.remove('active');
  });

  usageModal.addEventListener('click', (e) => {
    if (e.target === usageModal) {
      usageModal.classList.remove('active');
    }
  });

  // Init
  loadConfig();
  messageInput.focus();
})();
