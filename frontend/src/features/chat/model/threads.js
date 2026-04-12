const chatThreads = [
  createThread('New Chat'),
];

let activeChatId = chatThreads[0].id;

export function getChatThreads() {
  return chatThreads;
}

export function getActiveChatId() {
  return activeChatId;
}

export function setActiveChat(chatId) {
  const exists = chatThreads.some((thread) => thread.id === chatId);
  if (!exists) return false;

  activeChatId = chatId;
  return true;
}

export function createChatThread(title) {
  const nextIndex = chatThreads.length + 1;
  const thread = createThread(title || `New Chat ${nextIndex}`);
  chatThreads.unshift(thread);
  activeChatId = thread.id;
  return thread;
}

export function getMessages() {
  return getActiveThread().messages;
}

export function addMessage(message) {
  const thread = getActiveThread();
  thread.messages.push(message);
  maybeHydrateTitle(thread, message);
  return thread.messages.length - 1;
}

export function updateMessage(index, patch) {
  const thread = getActiveThread();
  const current = thread.messages[index];
  if (!current) return;

  thread.messages[index] = {
    ...current,
    ...patch,
  };
}

function getActiveThread() {
  return (
    chatThreads.find((thread) => thread.id === activeChatId) ??
    chatThreads[0]
  );
}

function createThread(title) {
  const threadTitle = title?.trim() || 'New Chat';

  return {
    id: crypto.randomUUID(),
    title: threadTitle,
    messages: [],
  };
}

function maybeHydrateTitle(thread, message) {
  if (message.role !== 'user') return;

  if (!/^New Chat(?: \d+)?$/i.test(thread.title)) return;

  const cleaned = message.text.trim().replace(/\s+/g, ' ');
  if (!cleaned) return;

  thread.title = cleaned.slice(0, 32);
}
