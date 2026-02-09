/**
 * Nour ✨ — Chatbot Widget pour bolibana.net
 */
(function () {
  'use strict';

  // Session ID unique par visiteur
  let sessionId = localStorage.getItem('nour_session_id');
  if (!sessionId) {
    sessionId = 'v_' + Math.random().toString(36).substr(2, 12);
    localStorage.setItem('nour_session_id', sessionId);
  }

  let isOpen = false;
  let isLoading = false;

  // ---- Créer le DOM ----
  const widget = document.createElement('div');
  widget.id = 'nour-chatbot';
  widget.innerHTML = `
    <!-- Bulle flottante -->
    <button id="nour-toggle" aria-label="Discuter avec Nour" title="Discuter avec Nour ✨">
      <svg id="nour-icon-chat" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="28" height="28">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/>
        <circle cx="8" cy="10" r="1.2"/>
        <circle cx="12" cy="10" r="1.2"/>
        <circle cx="16" cy="10" r="1.2"/>
      </svg>
      <svg id="nour-icon-close" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="28" height="28" style="display:none">
        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
      </svg>
    </button>

    <!-- Fenêtre de chat -->
    <div id="nour-window" style="display:none">
      <div id="nour-header">
        <div id="nour-header-info">
          <span id="nour-avatar">✨</span>
          <div>
            <strong>Nour</strong>
            <span id="nour-status">En ligne</span>
          </div>
        </div>
        <button id="nour-close" aria-label="Fermer">&times;</button>
      </div>
      <div id="nour-messages">
        <div class="nour-msg nour-bot">
          <div class="nour-bubble">
            Salut ! 👋 Je suis <strong>Nour</strong>, l'assistant IA de Konimba.<br>
            Comment puis-je t'aider ?
          </div>
        </div>
      </div>
      <form id="nour-form">
        <input id="nour-input" type="text" placeholder="Écris ton message..." autocomplete="off" maxlength="1000" />
        <button id="nour-send" type="submit" aria-label="Envoyer">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
          </svg>
        </button>
      </form>
    </div>
  `;
  document.body.appendChild(widget);

  // ---- Styles ----
  const style = document.createElement('style');
  style.textContent = `
    #nour-chatbot {
      --nour-primary: #6366f1;
      --nour-primary-dark: #4f46e5;
      --nour-bg: #ffffff;
      --nour-msg-bg: #f1f5f9;
      --nour-text: #1e293b;
      --nour-text-light: #64748b;
      --nour-radius: 16px;
      font-family: 'Inter', -apple-system, sans-serif;
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 9999;
    }

    /* Bulle flottante */
    #nour-toggle {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--nour-primary), var(--nour-primary-dark));
      color: white;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
      transition: transform 0.2s, box-shadow 0.2s;
    }
    #nour-toggle:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 28px rgba(99, 102, 241, 0.5);
    }

    /* Fenêtre */
    #nour-window {
      position: absolute;
      bottom: 76px;
      right: 0;
      width: 370px;
      max-width: calc(100vw - 32px);
      height: 500px;
      max-height: calc(100vh - 120px);
      background: var(--nour-bg);
      border-radius: var(--nour-radius);
      box-shadow: 0 12px 48px rgba(0,0,0,0.15);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      animation: nour-slide-up 0.3s ease;
    }
    @keyframes nour-slide-up {
      from { opacity: 0; transform: translateY(16px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* Header */
    #nour-header {
      background: linear-gradient(135deg, var(--nour-primary), var(--nour-primary-dark));
      color: white;
      padding: 14px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }
    #nour-header-info {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    #nour-avatar {
      font-size: 28px;
    }
    #nour-header strong {
      font-size: 15px;
      display: block;
    }
    #nour-status {
      font-size: 12px;
      opacity: 0.85;
    }
    #nour-close {
      background: none;
      border: none;
      color: white;
      font-size: 26px;
      cursor: pointer;
      padding: 0 4px;
      line-height: 1;
    }

    /* Messages */
    #nour-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .nour-msg {
      display: flex;
      max-width: 85%;
    }
    .nour-msg.nour-bot {
      align-self: flex-start;
    }
    .nour-msg.nour-user {
      align-self: flex-end;
    }
    .nour-bubble {
      padding: 10px 14px;
      border-radius: 14px;
      font-size: 14px;
      line-height: 1.5;
      word-break: break-word;
    }
    .nour-bot .nour-bubble {
      background: var(--nour-msg-bg);
      color: var(--nour-text);
      border-bottom-left-radius: 4px;
    }
    .nour-user .nour-bubble {
      background: var(--nour-primary);
      color: white;
      border-bottom-right-radius: 4px;
    }

    /* Typing indicator */
    .nour-typing .nour-bubble {
      display: flex;
      gap: 4px;
      padding: 14px 18px;
    }
    .nour-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--nour-text-light);
      animation: nour-bounce 1.4s infinite;
    }
    .nour-dot:nth-child(2) { animation-delay: 0.2s; }
    .nour-dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes nour-bounce {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-6px); }
    }

    /* Formulaire */
    #nour-form {
      display: flex;
      padding: 10px 12px;
      border-top: 1px solid #e2e8f0;
      gap: 8px;
      flex-shrink: 0;
    }
    #nour-input {
      flex: 1;
      border: 1px solid #e2e8f0;
      border-radius: 24px;
      padding: 10px 16px;
      font-size: 14px;
      outline: none;
      transition: border-color 0.2s;
      font-family: inherit;
    }
    #nour-input:focus {
      border-color: var(--nour-primary);
    }
    #nour-send {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: var(--nour-primary);
      color: white;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s;
      flex-shrink: 0;
    }
    #nour-send:hover {
      background: var(--nour-primary-dark);
    }
    #nour-send:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    /* Dark mode */
    @media (prefers-color-scheme: dark) {
      #nour-chatbot {
        --nour-bg: #1e293b;
        --nour-msg-bg: #334155;
        --nour-text: #f1f5f9;
        --nour-text-light: #94a3b8;
      }
      #nour-input {
        background: #334155;
        border-color: #475569;
        color: #f1f5f9;
      }
      #nour-form {
        border-color: #334155;
      }
    }

    /* Mobile */
    @media (max-width: 480px) {
      #nour-chatbot {
        bottom: 16px;
        right: 16px;
      }
      #nour-window {
        width: calc(100vw - 32px);
        height: calc(100vh - 100px);
        bottom: 70px;
        right: 0;
      }
    }
  `;
  document.head.appendChild(style);

  // ---- Logique ----
  const toggle = document.getElementById('nour-toggle');
  const window_ = document.getElementById('nour-window');
  const closeBtn = document.getElementById('nour-close');
  const form = document.getElementById('nour-form');
  const input = document.getElementById('nour-input');
  const messages = document.getElementById('nour-messages');
  const iconChat = document.getElementById('nour-icon-chat');
  const iconClose = document.getElementById('nour-icon-close');

  function toggleChat() {
    isOpen = !isOpen;
    window_.style.display = isOpen ? 'flex' : 'none';
    iconChat.style.display = isOpen ? 'none' : 'block';
    iconClose.style.display = isOpen ? 'block' : 'none';
    if (isOpen) input.focus();
  }

  toggle.addEventListener('click', toggleChat);
  closeBtn.addEventListener('click', toggleChat);

  function addMessage(text, isUser) {
    const div = document.createElement('div');
    div.className = 'nour-msg ' + (isUser ? 'nour-user' : 'nour-bot');
    div.innerHTML = '<div class="nour-bubble">' + text + '</div>';
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }

  function showTyping() {
    const div = document.createElement('div');
    div.className = 'nour-msg nour-bot nour-typing';
    div.id = 'nour-typing';
    div.innerHTML = '<div class="nour-bubble"><span class="nour-dot"></span><span class="nour-dot"></span><span class="nour-dot"></span></div>';
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function removeTyping() {
    const el = document.getElementById('nour-typing');
    if (el) el.remove();
  }

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const text = input.value.trim();
    if (!text || isLoading) return;

    addMessage(text, true);
    input.value = '';
    isLoading = true;
    document.getElementById('nour-send').disabled = true;
    showTyping();

    try {
      const res = await fetch('/chatbot/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      const data = await res.json();
      removeTyping();
      addMessage(data.response || data.error || 'Erreur inconnue', false);
    } catch (err) {
      removeTyping();
      addMessage("Désolé, je n'ai pas pu répondre. Réessaie ! 🙏", false);
    } finally {
      isLoading = false;
      document.getElementById('nour-send').disabled = false;
      input.focus();
    }
  });

  // Cacher le bouton WhatsApp quand le chat est à côté (optionnel)
  const waBtn = document.getElementById('floating-whatsapp');
  if (waBtn) {
    waBtn.style.right = '96px';
  }
})();
