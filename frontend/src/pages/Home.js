import { getVoiceSession } from '@/features/voice/model/session';
import { isSpeechEnabled } from '@/shared/model/preferences';
import { html } from '@/shared/lib/dom';
import { MainLayout } from '@/shared/layouts/MainLayout';
import '@/styles/pages/home.scss';

export function Home() {
  const session = getVoiceSession();
  const speechEnabled = isSpeechEnabled();

  return MainLayout(html`
    <div class="home voice-mode voice-mode--${session.state}">
      <div class="voice-mode__copy">
        <span class="voice-mode__eyebrow">Primary Screen</span>
        <h1>Voice Mode</h1>
        <p>
          This screen will become the main live voice interface. The orb stays calm while idle and
          pulses when Edith is actively speaking back.
        </p>
      </div>

      <div class="voice-mode__stage">
        <button class="voice-orb" type="button" data-action="voice-toggle" aria-label="Toggle voice mode">
          <span class="voice-orb__core"></span>
          <span class="voice-orb__ring voice-orb__ring--one"></span>
          <span class="voice-orb__ring voice-orb__ring--two"></span>
        </button>

        <div class="voice-mode__status">
          <div class="voice-chip">State: ${session.state}</div>
          <div class="voice-mode__transcript">${session.transcript}</div>
          <div class="voice-mode__response">${session.response}</div>
        </div>
      </div>
    </div>
  `);
}
