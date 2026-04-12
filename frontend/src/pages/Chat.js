import { getMessages } from '@/features/chat/model/threads';
import { isSpeechEnabled } from '@/shared/model/preferences';
import { html } from '@/shared/lib/dom';
import { MainLayout } from '@/shared/layouts/MainLayout';
import '@/styles/pages/chat.scss';

export function Chat() {
  const messages = getMessages();
  const speechEnabled = isSpeechEnabled();

  setTimeout(() => {
    const container = document.querySelector('.messages');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }

    document.querySelector('#chat-input')?.focus();
  });

  return MainLayout(html`
    <div class="chat">
      <h2>Chat</h2>

      <div class="messages">
        ${messages
          .map(
            (message) => `
          <div class="msg ${message.role} ${message.pending ? 'is-pending' : ''}">
            ${message.text}
          </div>
        `,
          )
          .join('')}
      </div>

      <div class="input-area">
        <input id="chat-input" placeholder="Type message..." />
        <button
          class="speech-toggle ${speechEnabled ? 'is-enabled' : 'is-disabled'}"
          data-action="toggle-speech"
          type="button"
        >
          ${speechEnabled ? 'Voice On' : 'Voice Off'}
        </button>
        <button data-action="send">Send</button>
        <button data-action="go-home">Back</button>
      </div>
    </div>
  `);
}
