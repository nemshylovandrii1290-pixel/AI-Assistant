const STORAGE_KEY = 'edith-preferences';

const preferences = loadPreferences();

export function getPreferences() {
  return preferences;
}

export function isSpeechEnabled() {
  return preferences.speechEnabled;
}

export function toggleSpeechEnabled() {
  preferences.speechEnabled = !preferences.speechEnabled;
  persistPreferences();
  return preferences.speechEnabled;
}

function loadPreferences() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : {};
    return {
      speechEnabled: parsed.speechEnabled ?? true,
    };
  } catch {
    return { speechEnabled: true };
  }
}

function persistPreferences() {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
}
