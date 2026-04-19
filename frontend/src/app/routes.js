import { registerRoute } from '@/app/router';
import { Home } from '@/pages/Home';
import { Settings } from '@/pages/Settings';
import { Login } from '@/pages/Login';

export function initRoutes() {
  registerRoute('/', Home);
  registerRoute('/settings', Settings);
  registerRoute('/login', Login);
}
