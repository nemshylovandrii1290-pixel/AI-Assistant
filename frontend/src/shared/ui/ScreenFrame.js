import { getBackendStatus } from '@/shared/model/backendStatus';
import { isSpeechEnabled } from '@/shared/model/preferences';
import '@/styles/layout/immersive-screen.scss';

export function ScreenFrame({ body, active = 'voice' }) {
  const backend = getBackendStatus();
  const speechEnabled = isSpeechEnabled();
  const showHomeClose = active !== 'voice';

  return `
    <section class="voice-screen">
      <div class="voice-screen__frame ${showHomeClose ? 'voice-screen__frame--with-close' : ''}">
        <header class="voice-screen__header">
          <div class="voice-screen__brand">AI ASSISTANT</div>
          <div class="voice-screen__status voice-screen__status--${backend.state}">
            <span class="voice-screen__status-dot"></span>
            <span>${backend.label}</span>
          </div>
        </header>

        ${
          showHomeClose
            ? `
          <button
            class="voice-screen__close-button"
            type="button"
            data-action="go-home"
            aria-label="Back to voice mode"
          >
            ×
          </button>
        `
            : ''
        }

        ${body}

        <footer class="voice-screen__footer">
          <button
            class="voice-screen__footer-button ${active === 'settings' ? 'is-active' : ''}"
            type="button"
            data-action="go-settings"
          >
            Settings
          </button>
          <button class="voice-screen__footer-button" type="button" data-action="toggle-speech">
            ${speechEnabled ? 'Mute' : 'Unmute'}
          </button>
          <button
            class="voice-screen__footer-button ${active === 'login' ? 'is-active' : ''}"
            type="button"
            data-action="login"
          >
            Login
          </button>
        </footer>
      </div>
    </section>
  `;
}
