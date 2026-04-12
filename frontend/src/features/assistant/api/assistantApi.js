import { postJson } from '@/shared/api/client';

export async function sendChatMessage({ message, speak }) {
  return postJson('/api/chat', { message, speak });
}

export async function sendVoiceTranscript({ transcript, speak }) {
  return postJson('/api/voice', { transcript, speak });
}
