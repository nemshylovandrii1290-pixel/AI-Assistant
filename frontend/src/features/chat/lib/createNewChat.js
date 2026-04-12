import { navigate } from '@/app/router';
import { render } from '@/shared/lib/dom';
import { Chat } from '@/pages/Chat';
import { createChatThread } from '@/features/chat/model/threads';

export function createNewChat() {
  createChatThread();
  navigate('/chat');
  render(Chat());
}
