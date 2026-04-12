import { getActiveChatId, getChatThreads } from '@/features/chat/model/threads';
import '@/styles/components/sidebar.scss';

export function Sidebar() {
  const activeChatId = getActiveChatId();
  const threads = getChatThreads();

  return `
    <aside class="sidebar">
      <div class="sidebar-top">
        <button class="sidebar-button" data-action="go-home">Voice Mode</button>
        <button class="sidebar-button" data-action="new-chat">New Chat</button>
      </div>

      <div class="sidebar-middle">
        <div class="chat-library">
          <div class="chat-library__title">Recent Chats</div>

          <div class="chat-list">
            ${threads
              .map(
                (thread) => `
                  <button
                    class="chat-item ${thread.id === activeChatId ? 'is-active' : ''}"
                    type="button"
                    data-action="open-chat"
                    data-chat-id="${thread.id}"
                  >
                    ${thread.title}
                  </button>
                `,
              )
              .join('')}
          </div>
        </div>
      </div>

      <div class="sidebar-bottom">
        <button class="sidebar-button" data-action="go-settings">Settings</button>
        <button class="sidebar-button" data-action="login">Login</button>
      </div>
    </aside>
  `;
}
