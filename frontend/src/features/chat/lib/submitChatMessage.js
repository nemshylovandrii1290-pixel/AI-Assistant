import { sendChatMessage } from '@/features/assistant/api/assistantApi';
import { addMessage, getMessages, updateMessage } from '@/features/chat/model/threads';
import { isSpeechEnabled } from '@/shared/model/preferences';
import { render } from '@/shared/lib/dom';
import { Chat } from '@/pages/Chat';

export async function submitChatMessage() {
  const input = document.querySelector('#chat-input');
  if (!input) return;

  const text = input.value;
  if (!text.trim()) return;

  addMessage({ role: 'user', text });
  input.value = '';
  render(Chat());

  const assistantIndex = addMessage({ role: 'ai', text: '', pending: true });
  render(Chat());

  try {
    const data = await sendChatMessage({
      message: text,
      speak: isSpeechEnabled(),
    });

    await typeAssistantReply(assistantIndex, data.reply || 'Я тут.');
  } catch (error) {
    updateMessage(assistantIndex, {
      text: error.message,
      pending: false,
    });
    render(Chat());
  }
}

async function typeAssistantReply(messageIndex, fullText) {
  updateMessage(messageIndex, { text: '', pending: true });

  for (let index = 1; index <= fullText.length; index += 1) {
    updateMessage(messageIndex, {
      text: fullText.slice(0, index),
      pending: true,
    });
    render(Chat());
    await wait(18);
  }

  updateMessage(messageIndex, {
    text: fullText,
    pending: false,
  });
  render(Chat());
}

function wait(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}
