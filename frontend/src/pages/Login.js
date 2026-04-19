import { html } from '@/shared/lib/dom';
import { ScreenFrame } from '@/shared/ui/ScreenFrame';
import '@/styles/pages/login.scss';

export function Login() {
  return ScreenFrame({
    active: 'login',
    body: html`
      <div class="login-page">
        <div class="login-card">
          <span class="login-card__eyebrow">Account Access</span>
          <h2>Login</h2>
          <p>Connect your account to sync future chats, presets, and assistant preferences across devices.</p>

          <div class="login-form">
            <label class="login-field">
              <span>Email</span>
              <input type="email" placeholder="you@example.com" />
            </label>

            <label class="login-field">
              <span>Password</span>
              <input type="password" placeholder="********" />
            </label>
          </div>

          <div class="login-actions">
            <button class="login-primary" type="button">Continue</button>
            <button class="login-secondary" type="button" data-action="go-home">Back Home</button>
          </div>
        </div>
      </div>
    `,
  });
}
