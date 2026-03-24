from collections import deque

import numpy as np
import sounddevice as sd

from utils.config import (
    AMBIENT_CHUNKS,
    CHUNK_DURATION,
    DYNAMIC_THRESHOLD_MULTIPLIER,
    LISTEN_DURATION,
    MIN_SPEECH_DURATION,
    PRE_ROLL_DURATION,
    SAMPLE_RATE,
    SILENCE_TIMEOUT,
    SPEECH_THRESHOLD,
)


def listen(duration=LISTEN_DURATION, stop_event=None, quiet=False):
    samplerate = SAMPLE_RATE
    chunk_size = int(samplerate * CHUNK_DURATION)
    max_chunks = max(1, int(duration / CHUNK_DURATION))
    silence_limit = max(1, int(SILENCE_TIMEOUT / CHUNK_DURATION))
    min_speech_chunks = max(1, int(MIN_SPEECH_DURATION / CHUNK_DURATION))
    pre_roll_limit = max(1, int(PRE_ROLL_DURATION / CHUNK_DURATION))
    recent_chunks = deque(maxlen=pre_roll_limit)
    ambient_levels = deque(maxlen=max(1, AMBIENT_CHUNKS))
    captured_chunks = []
    started = False
    silence_chunks = 0

    if not quiet:
        print("Listening...")

    with sd.InputStream(
        samplerate=samplerate,
        channels=1,
        dtype="int16",
        blocksize=chunk_size,
    ) as stream:
        for _ in range(max_chunks):
            if stop_event and stop_event.is_set():
                return None

            chunk, _ = stream.read(chunk_size)
            chunk_copy = chunk.copy()
            volume = float(np.abs(chunk_copy).mean())

            if not started:
                recent_chunks.append(chunk_copy)
                ambient_levels.append(volume)

            ambient_level = max(
                SPEECH_THRESHOLD,
                int(np.median(ambient_levels) * DYNAMIC_THRESHOLD_MULTIPLIER),
            )

            if volume >= ambient_level:
                if not started:
                    captured_chunks.extend(recent_chunks)
                    started = True

                silence_chunks = 0
                captured_chunks.append(chunk_copy)
                continue

            if started:
                captured_chunks.append(chunk_copy)
                silence_chunks += 1
                if silence_chunks >= silence_limit and len(captured_chunks) >= min_speech_chunks:
                    break

    if not captured_chunks:
        return None

    return np.concatenate(captured_chunks, axis=0)
