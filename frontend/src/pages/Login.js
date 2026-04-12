import { html } from '@/shared/lib/dom';
import { MainLayout } from '@/shared/layouts/MainLayout';
import '@/styles/pages/login.scss';

export function Login() {
  return MainLayout(html`
    <div class="login-page">
      <div class="login-card">
        <h2>Login</h2>
        <p>Connect your account to sync chats, settings, and future assistant features.</p>

        <div class="login-actions">
          <button class="login-primary" type="button">Continue</button>
          <button class="login-secondary" type="button" data-action="go-home">Back Home</button>
        </div>
      </div>
    </div>
  `);
}
