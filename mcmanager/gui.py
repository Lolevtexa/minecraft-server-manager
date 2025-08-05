import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import time

from mcmanager.tunnel import TunnelManager
from mcmanager.server import ServerManager

class AppGUI:
    def __init__(self, config):
        self.config = config
        self.root   = tk.Tk()
        self.root.title("Minecraft Server Manager")
        self.root.geometry("900x600")

        # Консоль
        self.console = scrolledtext.ScrolledText(self.root, state='disabled', height=25)
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Статусы
        self.server_status = tk.Label(self.root, text="Сервер: не запущен", fg="goldenrod")
        self.server_status.pack(pady=2)
        self.ssh_status    = tk.Label(self.root, text="SSH-туннель: не запущен", fg="goldenrod")
        self.ssh_status.pack(pady=2)

        # Внутренние флаги для статусов
        self.server_starting = False
        self.server_stopping = False
        self.tunnel_starting = False
        self.tunnel_stopping = False
        self.server_ready    = False

        # Менеджеры
        tcfg = config['tunnel']
        scfg = config['server']
        self.server = ServerManager(**scfg, console_append=self._on_server_output, on_ready=self._on_server_ready)
        self.tunnel = TunnelManager(**tcfg, console_append=self._on_tunnel_output)

        # Кнопки
        self._create_buttons()

        # Поток обновления статусов (мониторинг)
        threading.Thread(target=self._monitor_statuses, daemon=True).start()

    def _on_server_output(self, text):
        self.console_insert(text)
        if "Запуск сервера" in text:
            self.server_starting = False
        if "Сервер остановлен" in text:
            self.server_stopping = False
            self.server_ready = False  # если остановился, явно не готов
        self._update_status_labels()

    def _on_server_ready(self):
        self.server_ready = True
        self._update_status_labels()

    def _on_tunnel_output(self, text):
        self.console_insert(text)
        if "установлен" in text:
            self.tunnel_starting = False
        if "остановлен" in text:
            self.tunnel_stopping = False
        self._update_status_labels()

    def console_insert(self, text):
        self.console.config(state='normal')
        self.console.insert(tk.END, text + "\n")
        self.console.yview(tk.END)
        self.console.config(state='disabled')

    def _create_buttons(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=5)

        actions = [
            ("Start Server", self._start_server),
            ("Stop Server",  self._stop_server),
            ("Start Tunnel", self._start_tunnel),
            ("Stop Tunnel",  self._stop_tunnel),
            ("Restart Server", self._restart_server),
            ("New World",    lambda: self.server.restart_with_new_world(
                                  self.config['paths']['world'],
                                  self.config['paths']['backups'])),
            ("Help",         self._show_help),
        ]
        for i, (txt, cmd) in enumerate(actions):
            tk.Button(frame, text=txt, command=cmd).grid(row=0, column=i, padx=5)

    def _start_server(self):
        if not self.server.is_running() and not self.server_starting:
            self.server_starting = True
            self.server_stopping = False
        self.server_ready = False
        self._update_status_labels()
        threading.Thread(target=self.server.start, daemon=True).start()

    def _stop_server(self):
        if self.server.is_running() and not self.server_stopping:
            self.server_stopping = True
            self.server_starting = False
        self._update_status_labels()
        threading.Thread(target=self.server.stop, daemon=True).start()

    def _restart_server(self):
        self.server_stopping = False
        self.server_starting = True
        self.server_ready = False
        self._update_status_labels()
        threading.Thread(target=self.server.restart, daemon=True).start()

    def _start_tunnel(self):
        if not self.tunnel.is_running() and not self.tunnel_starting:
            self.tunnel_starting = True
            self.tunnel_stopping = False
        self._update_status_labels()
        threading.Thread(target=self.tunnel.start, daemon=True).start()

    def _stop_tunnel(self):
        if self.tunnel.is_running() and not self.tunnel_stopping:
            self.tunnel_stopping = True
            self.tunnel_starting = False
        self._update_status_labels()
        threading.Thread(target=self.tunnel.stop, daemon=True).start()

    def _show_help(self):
        msg = (
            "Команды:\n"
            "Start Server   – запустить сервер\n"
            "Stop Server    – остановить сервер\n"
            "Start Tunnel   – запустить SSH-туннель\n"
            "Stop Tunnel    – остановить SSH-туннель\n"
            "Restart Server – перезапустить сервер\n"
            "New World      – перезапустить с новым миром (архивация)\n"
        )
        messagebox.showinfo("Help", msg)

    def _update_status_labels(self):
        # SERVER
        if self.server_ready:
            self.server_status.config(text="Сервер: полностью запущен", fg="green")
        elif self.server_starting or (self.server.is_running() and not self.server_ready):
            self.server_status.config(text="Сервер: запускается", fg="red")
        elif self.server_stopping:
            self.server_status.config(text="Сервер: останавливается", fg="red")
        else:
            self.server_status.config(text="Сервер: не запущен", fg="goldenrod")
        # TUNNEL
        if self.tunnel_starting:
            self.ssh_status.config(text="SSH-туннель: запускается", fg="red")
        elif self.tunnel_stopping:
            self.ssh_status.config(text="SSH-туннель: останавливается", fg="red")
        elif self.tunnel.is_running():
            self.ssh_status.config(text="SSH-туннель: запущен", fg="green")
        else:
            self.ssh_status.config(text="SSH-туннель: не запущен", fg="goldenrod")

    def _monitor_statuses(self):
        while True:
            time.sleep(0.5)
            self._update_status_labels()

    def run(self):
        self.root.mainloop()
