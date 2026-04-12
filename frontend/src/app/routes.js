import { registerRoute } from '@/app/router';
import { Home } from '@/pages/Home';
import { Chat } from '@/pages/Chat';
import { Settings } from '@/pages/Settings';
import { Login } from '@/pages/Login';

export function initRoutes() {
  registerRoute('/', Home);
  registerRoute('/chat', Chat);
  registerRoute('/settings', Settings);
  registerRoute('/login', Login);
}
