import subprocess
import threading
import os

class TunnelManager:
    def __init__(self, user, host, local_port, remote_port, console_append):
        self.user        = user
        self.host        = host
        self.local_port  = local_port
        self.remote_port = remote_port
        self.console     = console_append
        self.proc        = None
        self.manual_stop = False
        self.lock        = threading.Lock()
        self.starting    = False

    def start(self):
        with self.lock:
            if self.is_running() or self.starting:
                self.console("SSH-туннель уже работает или запускается.")
                return
            self.starting = True
            self.manual_stop = False
        threading.Thread(target=self._connect_once, daemon=True).start()

    def _connect_once(self):
        try:
            with self.lock:
                if self.is_running() or self.manual_stop:
                    self.starting = False
                    return
            cmd = [
                "ssh", "-N",
                "-R", f"{self.local_port}:localhost:{self.remote_port}",
                f"{self.user}@{self.host}"
            ]
            self.proc = subprocess.Popen(cmd)
            self.console("SSH-туннель установлен.")
        except Exception as e:
            self.console(f"Ошибка туннеля: {e}")
        finally:
            with self.lock:
                self.starting = False

    def stop(self):
        with self.lock:
            self.manual_stop = True
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
                self.console("SSH-туннель остановлен вручную.")
                self.proc = None
            else:
                self.console("SSH-туннель не запущен.")
            self.starting = False

    def is_running(self):
        return self.proc is not None and self.proc.poll() is None