import { getBackendStatus } from '@/shared/model/backendStatus';
import { isSpeechEnabled } from '@/shared/model/preferences';
import { html } from '@/shared/lib/dom';
import { ScreenFrame } from '@/shared/ui/ScreenFrame';
import '@/styles/pages/settings.scss';

export function Settings() {
  const backend = getBackendStatus();
  const speechEnabled = isSpeechEnabled();

  return ScreenFrame({
    active: 'settings',
    body: html`
      <div class="settings-screen">
        <div class="settings-card">
          <span class="settings-card__eyebrow">System Control</span>
          <h2>Settings</h2>
          <p>Core preferences for Edith desktop mode and frontend voice interaction.</p>

          <div class="settings-grid">
            <div class="settings-item">
              <div class="settings-item__label">Backend API</div>
              <div class="settings-item__value status-${backend.state}">${backend.label}</div>
              <div class="settings-item__hint">${backend.detail}</div>
            </div>

            <div class="settings-item">
              <div class="settings-item__label">Voice replies</div>
              <div class="settings-item__value">${speechEnabled ? 'Enabled' : 'Muted'}</div>
              <div class="settings-item__hint">Use the footer button to mute or unmute spoken answers.</div>
            </div>

            <div class="settings-item">
              <div class="settings-item__label">Primary wake word</div>
              <div class="settings-item__value">Edit</div>
              <div class="settings-item__hint">Voice mode is designed to activate from the wake word.</div>
            </div>
          </div>
        </div>
      </div>
    `,
  });
}
