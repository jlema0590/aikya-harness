"""Bounded pipe reads with timeouts on platforms without selectable pipes."""
import os
import queue
import threading


class PipeReader:
    def __init__(self, stream):
        self.stream = stream
        self.pending = queue.Queue(maxsize=2)
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()

    def _put(self, value):
        while not self.stopped.is_set():
            try:
                self.pending.put(value, timeout=.05)
                return
            except queue.Full:
                pass

    def _read(self):
        try:
            while not self.stopped.is_set():
                chunk = os.read(self.stream.fileno(), 65536)
                self._put(chunk)
                if not chunk:
                    return
        except (OSError, ValueError) as error:
            self._put(error)

    def read(self, timeout):
        try:
            value = self.pending.get(timeout=timeout)
        except queue.Empty:
            return None
        if isinstance(value, Exception):
            raise value
        return value

    def close(self):
        # The owner terminates/waits for the process and closes its pipe first.
        self.stopped.set()
        self.thread.join(1)
