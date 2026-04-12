import { markBackendOffline, markBackendOnline } from '@/shared/model/backendStatus';
import { API_BASE_URL } from '@/shared/config/api';

export async function postJson(path, payload) {
  let lastError = null;

  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const response = await fetch(`${API_BASE_URL}${path}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const error = new Error(data.error || friendlyMessageFromStatus(response.status));
        error.status = response.status;
        throw error;
      }

      markBackendOnline();
      return data;
    } catch (error) {
      lastError = error;

      if (attempt < 2) {
        await wait(500 * (attempt + 1));
        continue;
      }

      markBackendOffline(toFriendlyErrorMessage(error));
    }
  }

  throw new Error(toFriendlyErrorMessage(lastError));
}

function friendlyMessageFromStatus(status) {
  if (status >= 500) {
    return 'The assistant backend is running, but it failed while processing your request.';
  }

  if (status === 404) {
    return 'The assistant API route was not found.';
  }

  if (status === 400) {
    return 'The request was incomplete. Try again.';
  }

  return 'Request failed.';
}

function toFriendlyErrorMessage(error) {
  if (!error) {
    return 'Could not reach Edith backend. Start the app with npm run dev.';
  }

  const message = String(error.message || '');

  if (message.includes('Failed to fetch')) {
    return 'Could not reach Edith backend. Start the app with npm run dev.';
  }

  if (message.includes('NetworkError')) {
    return 'Network connection to the Edith backend was interrupted.';
  }

  return message;
}

function wait(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}
