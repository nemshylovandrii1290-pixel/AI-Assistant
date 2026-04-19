import { getVoiceSession } from '@/features/voice/model/session';
import { html } from '@/shared/lib/dom';
import { ScreenFrame } from '@/shared/ui/ScreenFrame';
import '@/styles/pages/home.scss';

export function Home() {
  const session = getVoiceSession();
  const screenState =
    session.state === 'listening'
      ? 'voice-screen--listening'
      : session.state === 'responding'
        ? 'voice-screen--responding'
        : 'voice-screen--idle';

  return ScreenFrame({
    active: 'voice',
    body: html`
      <div class="voice-screen__body ${screenState}">
        <div class="voice-screen__stars"></div>

        <div class="voice-screen__visual">
          <div class="voice-wave voice-wave--one" aria-hidden="true">
            <div class="voice-wave__track">
              <svg viewBox="0 0 1200 280" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="waveGradientA" x1="0%" y1="50%" x2="100%" y2="50%">
                    <stop offset="0%" stop-color="#42e9ff" stop-opacity="0.15" />
                    <stop offset="25%" stop-color="#67f2ff" stop-opacity="0.95" />
                    <stop offset="55%" stop-color="#ff6ef6" stop-opacity="0.95" />
                    <stop offset="100%" stop-color="#54a7ff" stop-opacity="0.18" />
                  </linearGradient>
                </defs>

                <path d="M0 140 C 100 80, 180 200, 280 140 S 460 80, 560 140 740 200, 840 140 1020 80, 1200 140" fill="none" stroke="url(#waveGradientA)" stroke-width="5" stroke-linecap="round" />
                <path d="M0 152 C 110 95, 190 208, 290 152 S 470 95, 570 152 750 208, 850 152 1030 95, 1200 152" fill="none" stroke="url(#waveGradientA)" stroke-width="2" stroke-linecap="round" opacity="0.9" />
                <path d="M0 128 C 110 78, 205 190, 305 128 S 485 78, 585 128 765 190, 865 128 1045 78, 1200 128" fill="none" stroke="url(#waveGradientA)" stroke-width="2" stroke-linecap="round" opacity="0.65" />
              </svg>
              <svg viewBox="0 0 1200 280" preserveAspectRatio="none">
                <path d="M0 140 C 100 80, 180 200, 280 140 S 460 80, 560 140 740 200, 840 140 1020 80, 1200 140" fill="none" stroke="url(#waveGradientA)" stroke-width="5" stroke-linecap="round" />
                <path d="M0 152 C 110 95, 190 208, 290 152 S 470 95, 570 152 750 208, 850 152 1030 95, 1200 152" fill="none" stroke="url(#waveGradientA)" stroke-width="2" stroke-linecap="round" opacity="0.9" />
                <path d="M0 128 C 110 78, 205 190, 305 128 S 485 78, 585 128 765 190, 865 128 1045 78, 1200 128" fill="none" stroke="url(#waveGradientA)" stroke-width="2" stroke-linecap="round" opacity="0.65" />
              </svg>
            </div>
          </div>

          <div class="voice-wave voice-wave--two" aria-hidden="true">
            <div class="voice-wave__track">
              <svg viewBox="0 0 1200 280" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="waveGradientB" x1="0%" y1="50%" x2="100%" y2="50%">
                    <stop offset="0%" stop-color="#5cf3ff" stop-opacity="0.08" />
                    <stop offset="35%" stop-color="#7f8cff" stop-opacity="0.88" />
                    <stop offset="70%" stop-color="#f58bff" stop-opacity="0.88" />
                    <stop offset="100%" stop-color="#59eeff" stop-opacity="0.08" />
                  </linearGradient>
                </defs>

                <path d="M0 140 C 110 200, 205 78, 305 140 S 485 200, 585 140 765 78, 865 140 1045 200, 1200 140" fill="none" stroke="url(#waveGradientB)" stroke-width="4" stroke-linecap="round" />
                <path d="M0 126 C 100 182, 190 85, 290 126 S 470 182, 570 126 750 85, 850 126 1030 182, 1200 126" fill="none" stroke="url(#waveGradientB)" stroke-width="1.5" stroke-linecap="round" opacity="0.9" />
                <path d="M0 156 C 100 214, 205 102, 305 156 S 485 214, 585 156 765 102, 865 156 1045 214, 1200 156" fill="none" stroke="url(#waveGradientB)" stroke-width="1.5" stroke-linecap="round" opacity="0.7" />
              </svg>
              <svg viewBox="0 0 1200 280" preserveAspectRatio="none">
                <path d="M0 140 C 110 200, 205 78, 305 140 S 485 200, 585 140 765 78, 865 140 1045 200, 1200 140" fill="none" stroke="url(#waveGradientB)" stroke-width="4" stroke-linecap="round" />
                <path d="M0 126 C 100 182, 190 85, 290 126 S 470 182, 570 126 750 85, 850 126 1030 182, 1200 126" fill="none" stroke="url(#waveGradientB)" stroke-width="1.5" stroke-linecap="round" opacity="0.9" />
                <path d="M0 156 C 100 214, 205 102, 305 156 S 485 214, 585 156 765 102, 865 156 1045 214, 1200 156" fill="none" stroke="url(#waveGradientB)" stroke-width="1.5" stroke-linecap="round" opacity="0.7" />
              </svg>
            </div>
          </div>

          <div class="voice-screen__orb" aria-hidden="true">
            <span class="voice-screen__orb-glow"></span>
            <span class="voice-screen__orb-core"></span>
            <span class="voice-screen__orb-text">
              ${session.state === 'listening' ? 'Listening...' : session.state === 'responding' ? 'Responding...' : 'Edit'}
            </span>
          </div>
        </div>

        <div class="voice-screen__meta">
          <div class="voice-screen__transcript">${session.transcript}</div>
          <div class="voice-screen__response">${session.response}</div>
        </div>
      </div>
    `,
  });
}
