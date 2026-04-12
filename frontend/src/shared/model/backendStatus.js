const backendStatus = {
  state: 'checking',
  label: 'Checking',
  detail: 'Trying to reach the backend API.',
};

let healthTimer = null;

export function getBackendStatus() {
  return backendStatus;
}

export function startBackendHealthPolling(onChange) {
  stopBackendHealthPolling();

  const runCheck = async () => {
    const nextState = await pingBackend();
    const changed =
      nextState.state !== backendStatus.state ||
      nextState.label !== backendStatus.label ||
      nextState.detail !== backendStatus.detail;

    Object.assign(backendStatus, nextState);

    if (changed && onChange) {
      onChange();
    }
  };

  void runCheck();
  healthTimer = window.setInterval(() => {
    void runCheck();
  }, 5000);
}

export function stopBackendHealthPolling() {
  if (healthTimer) {
    window.clearInterval(healthTimer);
    healthTimer = null;
  }
}

export function markBackendOffline(detail = 'Backend API is offline.') {
  backendStatus.state = 'offline';
  backendStatus.label = 'Offline';
  backendStatus.detail = detail;
}

export function markBackendOnline() {
  backendStatus.state = 'online';
  backendStatus.label = 'Online';
  backendStatus.detail = 'Backend API is ready.';
}

async function pingBackend() {
  try {
    const response = await fetch('/api/health');
    if (!response.ok) {
      return {
        state: 'offline',
        label: 'Offline',
        detail: 'Backend API answered with an error.',
      };
    }

    return {
      state: 'online',
      label: 'Online',
      detail: 'Backend API is ready.',
    };
  } catch {
    return {
      state: 'offline',
      label: 'Offline',
      detail: 'Start frontend with npm run dev so the backend API launches too.',
    };
  }
}
