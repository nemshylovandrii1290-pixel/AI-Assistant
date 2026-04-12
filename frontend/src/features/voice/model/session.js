const voiceSession = {
  state: 'idle',
  transcript: 'Say "Edit" to wake the assistant.',
  response: 'Waiting for your voice command.',
  supported: typeof window !== 'undefined' && Boolean(getSpeechRecognitionClass()),
};

let recognition = null;

export function getVoiceSession() {
  return voiceSession;
}

export function startVoiceRecognition({ onResult, onError }) {
  const SpeechRecognition = getSpeechRecognitionClass();
  if (!SpeechRecognition) {
    voiceSession.supported = false;
    voiceSession.state = 'idle';
    voiceSession.response = 'Speech recognition is not supported in this browser.';
    return false;
  }

  voiceSession.supported = true;
  voiceSession.state = 'listening';
  voiceSession.transcript = 'Listening...';
  voiceSession.response = 'Speak naturally, I am ready.';

  recognition = new SpeechRecognition();
  recognition.lang = 'uk-UA';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (event) => {
    const transcript = event.results?.[0]?.[0]?.transcript?.trim() || '';
    voiceSession.transcript = transcript || 'Nothing detected.';
    voiceSession.state = 'responding';

    if (transcript && onResult) {
      onResult(transcript);
    }
  };

  recognition.onerror = (event) => {
    voiceSession.state = 'idle';
    voiceSession.response = `Voice error: ${event.error}`;
    if (onError) {
      onError(event.error);
    }
  };

  recognition.onend = () => {
    recognition = null;
    if (voiceSession.state === 'listening') {
      voiceSession.state = 'idle';
      voiceSession.response = 'Listening stopped.';
    }
  };

  recognition.start();
  return true;
}

export function stopVoiceRecognition() {
  if (recognition) {
    recognition.stop();
    recognition = null;
  }

  voiceSession.state = 'idle';
}

export function setVoiceResponse(reply) {
  voiceSession.state = 'responding';
  voiceSession.response = reply;
}

export function resetVoiceSession() {
  stopVoiceRecognition();
  voiceSession.transcript = 'Say "Edit" to wake the assistant.';
  voiceSession.response = 'Waiting for your voice command.';
}

function getSpeechRecognitionClass() {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

export const session = {
  state: 'idle', // idle | listening | speaking
  transcript: '',
  response: '',
};
