import '@/styles/main.scss';
import { initRoutes } from '@/app/routes';
import { initRouter, navigate, refreshRoute } from '@/app/router';
import { syncVoiceModeForRoute } from '@/features/voice/lib/toggleVoiceMode';
import { toggleSpeechEnabled } from '@/shared/model/preferences';
import { startBackendHealthPolling } from '@/shared/model/backendStatus';

initRoutes();
initRouter();
let lastStatus = null;

startBackendHealthPolling((status) => {
  if (status === lastStatus) return;

  lastStatus = status;
  refreshRoute();
});

let currentPath = null;

window.addEventListener('edith:route-changed', (event) => {
  const path = event.detail.path;

  if (path === currentPath) return;
  currentPath = path;

  syncVoiceModeForRoute(path);
});

navigate('/');

document.addEventListener('click', (event) => {
  const action = event.target.dataset.action;

  if (!action) return;

  if (action === 'go-home') {
    navigate('/');
    return;
  }

  if (action === 'go-settings') {
    navigate('/settings');
    return;
  }

  if (action === 'login') {
    navigate('/login');
    return;
  }

  if (action === 'toggle-speech') {
    toggleSpeechEnabled();
    refreshRoute();
  }
});
