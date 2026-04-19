const WAKE_WORDS = ['edit', 'едіт', 'едит'];
const ASSISTANT_ECHO_PATTERNS = [
  'привіт, я тут',
  'привіт я тут',
  'що будемо робити',
  'слухаю',
  'я тут',
];

const voiceSession = {
  state: 'idle',
  transcript: 'Say "Edit" to wake the assistant.',
  response: 'Waiting for your voice command.',
  supported: typeof window !== 'undefined' && Boolean(getSpeechRecognitionClass()),
};

let recognition = null;
let shouldStayActive = false;
let pausedForReply = false;
let awaitingCommand = false;
let restartTimer = null;
let transcriptHandler = null;
let errorHandler = null;

export function getVoiceSession() {
  return voiceSession;
}

export function startVoiceRecognitionLoop({ onTranscript, onError }) {
  const SpeechRecognition = getSpeechRecognitionClass();
  if (!SpeechRecognition) {
    voiceSession.supported = false;
    voiceSession.state = 'idle';
    voiceSession.response = 'Speech recognition is not supported in this browser.';
    return false;
  }

  voiceSession.supported = true;
  shouldStayActive = true;
  pausedForReply = false;
  transcriptHandler = onTranscript;
  errorHandler = onError;

  if (recognition || restartTimer) {
    voiceSession.state = 'listening';
    voiceSession.response = awaitingCommand ? 'Listening for your command.' : 'Listening for the wake word.';
    return true;
  }

  voiceSession.state = 'listening';
  voiceSession.transcript = 'Say "Edit" to wake the assistant.';
  voiceSession.response = 'Listening for the wake word.';
  scheduleRestart(0);
  return true;
}

export function stopVoiceRecognition({ clearText = false } = {}) {
  shouldStayActive = false;
  pausedForReply = false;
  awaitingCommand = false;
  transcriptHandler = null;
  errorHandler = null;

  if (restartTimer) {
    window.clearTimeout(restartTimer);
    restartTimer = null;
  }

  if (recognition) {
    recognition.onend = null;
    recognition.stop();
    recognition = null;
  }

  voiceSession.state = 'idle';
  if (clearText) {
    voiceSession.transcript = 'Say "Edit" to wake the assistant.';
    voiceSession.response = 'Waiting for your voice command.';
  }
}

export function setVoiceResponse(reply, { resume = true, spoken = false, delayMs = null } = {}) {
  voiceSession.state = 'responding';
  voiceSession.response = reply;

  pausedForReply = false;

  if (!resume || !shouldStayActive) {
    return;
  }

  pausedForReply = false;

  const computedDelay =
    delayMs ??
    Math.min(
      Math.max(reply.length * (spoken ? 80 : 24) + (spoken ? 1400 : 0), spoken ? 3400 : 1800),
      spoken ? 7600 : 5200,
    );

  scheduleRestart(computedDelay);
}

function startRecognitionNow() {
  if (!shouldStayActive || pausedForReply) {
    return;
  }

  if (recognition) {
    try {
      recognition.stop();
    } catch {}
    recognition = null;
  }

  const SpeechRecognition = getSpeechRecognitionClass();
  if (!SpeechRecognition) {
    voiceSession.supported = false;
    voiceSession.state = 'idle';
    voiceSession.response = 'Speech recognition is not supported in this browser.';
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = 'uk-UA';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.continuous = false;

  recognition.onresult = (event) => {
    const transcript = event.results?.[0]?.[0]?.transcript?.trim() || '';
    handleRecognitionResult(transcript);
  };

  recognition.onerror = (event) => {
    recognition = null;

    if (event.error === 'aborted') {
      return;
    }

    voiceSession.state = 'idle';
    voiceSession.response = `Voice error: ${event.error}`;

    if (errorHandler) {
      errorHandler(event.error);
    }

    if (shouldStayActive) {
      scheduleRestart(900);
    }
  };

  recognition.onend = () => {
    recognition = null;

    if (shouldStayActive) {
      setTimeout(() => {
        startRecognitionNow();
      }, 200);
    }
  };

  recognition.start();
}

function handleRecognitionResult(transcript) {
  const cleanTranscript = transcript.trim();
  if (!cleanTranscript) {
    voiceSession.state = 'listening';
    voiceSession.transcript = awaitingCommand
      ? 'Listening for your command.'
      : 'Say "Edit" to wake the assistant.';
    voiceSession.response = awaitingCommand
      ? 'Listening for your command.'
      : 'Listening for the wake word.';
    return;
  }

  const normalized = cleanTranscript.toLowerCase();

  if (awaitingCommand && ASSISTANT_ECHO_PATTERNS.some((pattern) => normalized.includes(pattern))) {
    voiceSession.state = 'listening';
    voiceSession.transcript = 'Listening for your command.';
    voiceSession.response = 'Listening for your command.';
    return;
  }

  if (awaitingCommand) {
    awaitingCommand = false;
    pausedForReply = false;
    voiceSession.state = 'responding';
    voiceSession.transcript = cleanTranscript;
    voiceSession.response = 'Thinking...';

    if (transcriptHandler) {
      transcriptHandler(cleanTranscript);
    }
    return;
  }

  const hasWakeWord = WAKE_WORDS.some((word) => normalized.includes(word));
  if (!hasWakeWord) {
    voiceSession.state = 'listening';
    voiceSession.transcript = cleanTranscript;
    voiceSession.response = 'Listening for "Edit"...';
    return;
  }

  const command = stripWakeWords(normalized);
  voiceSession.transcript = cleanTranscript;

  if (!command) {
    awaitingCommand = true;
    pausedForReply = false;
    voiceSession.state = 'responding';
    voiceSession.response = 'Слухаю...';

    return;
  }

  pausedForReply = false;
  voiceSession.state = 'responding';
  voiceSession.response = 'Thinking...';

  if (transcriptHandler) {
    transcriptHandler(command);
  }
}

function stripWakeWords(text) {
  let stripped = text;
  for (const word of WAKE_WORDS) {
    stripped = stripped.replaceAll(word, ' ');
  }
  return stripped.replace(/\s+/g, ' ').trim();
}

function scheduleRestart(delay) {
  if (!shouldStayActive) {
    return;
  }

  if (restartTimer) {
    window.clearTimeout(restartTimer);
  }

  restartTimer = window.setTimeout(() => {
    restartTimer = null;
    voiceSession.state = 'listening';
    voiceSession.transcript = awaitingCommand
      ? 'Listening for your command.'
      : 'Say "Edit" to wake the assistant.';
    if (voiceSession.response === 'Thinking...' || voiceSession.response === 'Слухаю...') {
      voiceSession.response = awaitingCommand
        ? 'Listening for your command.'
        : 'Listening for the wake word.';
    }
    startRecognitionNow();
  }, delay);
}

function getSpeechRecognitionClass() {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}
