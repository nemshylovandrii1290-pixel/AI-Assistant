import { sendVoiceTranscript } from '@/features/assistant/api/assistantApi';
import {
  getVoiceSession,
  resetVoiceSession,
  setVoiceResponse,
  startVoiceRecognition,
  stopVoiceRecognition,
} from '@/features/voice/model/session';
import { refreshRoute } from '@/app/router';
import { isSpeechEnabled } from '@/shared/model/preferences';

export async function toggleVoiceMode() {
  const session = getVoiceSession();

  if (session.state === 'listening') {
    stopVoiceRecognition();
    refreshRoute();
    return;
  }

  const started = startVoiceRecognition({
    onResult: async (transcript) => {
      refreshRoute();

      try {
        const data = await sendVoiceTranscript({
          transcript,
          speak: isSpeechEnabled(),
        });

        setVoiceResponse(data.reply || 'Я почула тебе.');
      } catch (error) {
        setVoiceResponse(error.message);
      }

      refreshRoute();
    },
    onError: () => {
      refreshRoute();
    },
  });

  if (started) {
    refreshRoute();
  }
}

export function resetVoiceMode() {
  resetVoiceSession();
  refreshRoute();
}
