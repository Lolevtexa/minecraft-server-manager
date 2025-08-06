import subprocess
import threading
import time
import os
import shutil
from datetime import datetime

class ServerManager:
    def __init__(self, server_dir, jar_file, mem_opts, console_append, on_ready=None):
        self.server_dir = server_dir
        self.jar = os.path.join(server_dir, jar_file)
        self.mem_opts = mem_opts
        self.console  = console_append
        self.on_ready = on_ready
        self.proc     = None
        self.ready    = False

    def start(self):
        if self.is_running():
            self.console("Сервер уже запущен.")
            return
        self.ready = False
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        cmd = ["java"] + self.mem_opts.split() + ["-jar", self.jar, "--nogui"]
        self.proc = subprocess.Popen(cmd, cwd=self.server_dir,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     text=True)
        self.console("Запуск сервера...")
        for line in self.proc.stdout:
            self.console(line.rstrip())
            if "Done (" in line and 'For help, type "help"' in line:
                self.ready = True
                if self.on_ready:
                    self.on_ready()
        self.ready = False

    def stop(self):
        if self.is_running():
            self.proc.terminate()
            self.console("Сервер остановлен.")
        else:
            self.console("Сервер не запущен.")

    def restart(self):
        self.stop()
        time.sleep(2)
        self.start()

    def restart_with_new_world(self, backup_dir):
        world_dir = os.path.join(self.server_dir, "world")
        if os.path.isdir(world_dir):
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            base = os.path.join(backup_dir, f"world_{ts}")
            shutil.make_archive(base, 'zip', world_dir)
            shutil.rmtree(world_dir)
            self.console(f"Мир архивирован в {base}.zip")
        else:
            self.console("Папка мира не найдена.")
        self.start()

    def is_running(self):
        return self.proc is not None and self.proc.poll() is None

    def is_ready(self):
        return self.ready