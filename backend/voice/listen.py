import queue
import threading
import time

import numpy as np
import sounddevice as sd

from backend.utils.config import CHUNK_DURATION, SAMPLE_RATE


class AudioStream:
    def __init__(self, samplerate=SAMPLE_RATE, channels=1, dtype="int16"):
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.chunk_size = max(1, int(self.samplerate * CHUNK_DURATION))
        self.queue = queue.Queue(maxsize=128)
        self._stream = None
        self._lock = threading.Lock()
        self._started = False

    def _callback(self, indata, frames, time_info, status):
        if status:
            return

        chunk = indata.copy()
        try:
            self.queue.put_nowait(chunk)
        except queue.Full:
            try:
                self.queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.queue.put_nowait(chunk)
            except queue.Full:
                pass

    def start(self):
        with self._lock:
            if self._started:
                return self

            self._stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype=self.dtype,
                blocksize=self.chunk_size,
                callback=self._callback,
            )
            self._stream.start()
            self._started = True
        return self

    def stop(self):
        with self._lock:
            if not self._started:
                return

            try:
                self._stream.stop()
            finally:
                self._stream.close()
                self._stream = None
                self._started = False

    def read_chunk(self, timeout=0.1):
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def iter_chunks(self, stop_event=None, timeout=0.1):
        while not (stop_event and stop_event.is_set()):
            chunk = self.read_chunk(timeout=timeout)
            if chunk is not None:
                yield chunk


_default_stream = AudioStream()


def start_stream():
    return _default_stream.start()


def get_chunk(timeout=0.1):
    return _default_stream.read_chunk(timeout=timeout)


def stop_stream():
    _default_stream.stop()


def listen(duration=1.5, stop_event=None, quiet=False):
    stream = AudioStream().start()
    chunks = []
    deadline = time.monotonic() + duration

    try:
        while time.monotonic() < deadline:
            if stop_event and stop_event.is_set():
                return None

            chunk = stream.read_chunk(timeout=0.1)
            if chunk is not None:
                chunks.append(chunk)
    finally:
        stream.stop()

    if not chunks:
        return None

    return np.concatenate(chunks, axis=0)
