import { sendVoiceTranscript } from '@/features/assistant/api/assistantApi';
import {
  getVoiceSession,
  setVoiceResponse,
  startVoiceRecognitionLoop,
  stopVoiceRecognition,
} from '@/features/voice/model/session';
import { refreshRoute } from '@/app/router';
import { isSpeechEnabled } from '@/shared/model/preferences';

export function syncVoiceModeForRoute(path) {
  if (path !== '/') {
    return;
  }

  const session = getVoiceSession();
  if (!session.supported) {
    refreshRoute();
    return;
  }

  let isSpeaking = false;

  startVoiceRecognitionLoop({
    onTranscript: async (transcript) => {
      if (isSpeaking) return;

      const spoken = isSpeechEnabled();
      const isWakeOnly = transcript === '__wake__';

      try {
        const data = await sendVoiceTranscript({
          transcript: isWakeOnly ? 'edit' : transcript,
          speak: isWakeOnly ? false : spoken,
        });

        isSpeaking = true;

        setVoiceResponse(data.reply || 'Я почула тебе.', {
          spoken: isWakeOnly ? false : spoken,
          delayMs: isWakeOnly && spoken ? 7000 : null,
          onEnd: () => {
            isSpeaking = false;
            startVoiceRecognitionLoopAgain(); // 👈 треба буде зробити
          },
        });
      } catch (error) {
        isSpeaking = false;

        setVoiceResponse(error.message || 'Could not reach Edith backend.', {
          spoken: false,
        });

        startVoiceRecognitionLoopAgain();
      }

    },
  });

}
