import '@/styles/main.scss';
import { initRoutes } from '@/app/routes';
import { initRouter, navigate, refreshRoute } from '@/app/router';
import { createNewChat } from '@/features/chat/lib/createNewChat';
import { submitChatMessage } from '@/features/chat/lib/submitChatMessage';
import { setActiveChat } from '@/features/chat/model/threads';
import { toggleVoiceMode, resetVoiceMode } from '@/features/voice/lib/toggleVoiceMode';
import { toggleSpeechEnabled } from '@/shared/model/preferences';
import { startBackendHealthPolling } from '@/shared/model/backendStatus';

initRoutes();
initRouter();
startBackendHealthPolling(() => {
  refreshRoute();
});
navigate('/');

document.addEventListener('click', (event) => {
  const action = event.target.dataset.action;

  if (!action) return;

  if (action === 'go-chat') {
    navigate('/chat');
    return;
  }

  if (action === 'go-home') {
    navigate('/');
    return;
  }

  if (action === 'go-settings') {
    navigate('/settings');
    return;
  }

  if (action === 'new-chat') {
    createNewChat();
    return;
  }

  if (action === 'login') {
    navigate('/login');
    return;
  }

  if (action === 'voice-toggle') {
    toggleVoiceMode();
    return;
  }

  if (action === 'toggle-speech') {
    toggleSpeechEnabled();
    refreshRoute();
    return;
  }

  if (action === 'voice-reset') {
    resetVoiceMode();
    return;
  }

  if (action === 'open-chat') {
    const chatId = event.target.dataset.chatId;
    if (!chatId) return;

    setActiveChat(chatId);
    navigate('/chat');
    return;
  }

  if (action === 'send') {
    void submitChatMessage();
  }
});

document.addEventListener('keydown', (event) => {
  if (event.key !== 'Enter') return;

  const input = document.querySelector('#chat-input');
  if (!input) return;

  void submitChatMessage();
});
