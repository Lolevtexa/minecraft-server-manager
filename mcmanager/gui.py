import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import threading
import time
import os

from mcmanager.tunnel import TunnelManager
from mcmanager.server import ServerManager
from mcmanager.config_manager import ConfigManager

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, config, on_save):
        super().__init__(parent)
        self.title("Настройки")
        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)
        self.config_dict = config
        self.on_save = on_save
        self.entries = {}
        self.min_mem_var = tk.StringVar()
        self.max_mem_var = tk.StringVar()

        mem = config['server'].get('mem_opts', '')
        try:
            parts = mem.split()
            ms = next(p for p in parts if p.startswith('-Xms'))
            mx = next(p for p in parts if p.startswith('-Xmx'))
            self.min_mem_var.set(ms.lstrip('-Xms').rstrip('M'))
            self.max_mem_var.set(mx.lstrip('-Xmx').rstrip('M'))
        except StopIteration:
            self.min_mem_var.set("512")
            self.max_mem_var.set("2048")

        sections = {
            'server': {
                'jar_file': 'Jar-файл (ядро сервера)'
            },
            'paths': {
                'server_files': 'Папка с файлами сервера',
                'backups':      'Папка с резервными копиями'
            },
            'tunnel': {
                'user':        'SSH-пользователь',
                'host':        'SSH-хост',
                'local_port':  'Локальный порт',
                'remote_port': 'Удалённый порт'
            }
        }

        row = 0
        # Сначала стандартные поля
        for section, params in sections.items():
            lbl = tk.Label(self, text=section.capitalize(), font=('Arial', 10, 'bold'))
            lbl.grid(row=row, column=0, columnspan=3, sticky='w', pady=(10,0))
            row += 1
            for key, label in params.items():
                tk.Label(self, text=label).grid(row=row, column=0, sticky='e', padx=5, pady=2)
                ent = tk.Entry(self)
                ent.insert(0, str(config.get(section, {}).get(key, "")))
                ent.grid(row=row, column=1, sticky='we', padx=5, pady=2)
                self.entries[f"{section}.{key}"] = ent

                # для путей — кнопка выбора папки
                if section == 'paths':
                    btn = tk.Button(self, text="…", width=3,
                        command=lambda e=ent: self._browse_folder(e))
                    btn.grid(row=row, column=2, padx=(0,5))

                # для выбора .jar (ядра сервера)
                if section == 'server' and key == 'jar_file':
                    btn = tk.Button(self, text="…", width=3,
                        command=lambda e=ent: self._browse_jar_file(e))
                    btn.grid(row=row, column=2, padx=(0,5))

                row += 1

            if section == 'server':
                lbl_min = tk.Label(self, text="Мин. ОЗУ (МБ)").grid(row=row, column=0, sticky='e', padx=5, pady=2)
                ent_min = tk.Entry(self, textvariable=self.min_mem_var)
                ent_min.grid(row=row, column=1, sticky='we', padx=5, pady=2)
                row += 1

                lbl_max = tk.Label(self, text="Макс. ОЗУ (МБ)").grid(row=row, column=0, sticky='e', padx=5, pady=2)
                ent_max = tk.Entry(self, textvariable=self.max_mem_var)
                ent_max.grid(row=row, column=1, sticky='we', padx=5, pady=2)
                row += 1

        # Кнопки
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10)
        tk.Button(btn_frame, text="Сохранить", command=self._save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена",   command=self.destroy).pack(side=tk.LEFT)
        self.columnconfigure(1, weight=1)

    def _browse_folder(self, entry_widget):
        path = filedialog.askdirectory(parent=self, initialdir=os.getcwd())
        if path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, path)

    def _browse_jar_file(self, entry_widget):
        path = filedialog.askopenfilename(
            parent=self,
            title="Выберите ядро сервера",
            initialdir=os.getcwd(),
            filetypes=[("Jar files", "*.jar")]
        )
        if path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, path)

    def _save(self):
        cfg = self.config_dict
        # Сначала обычные поля
        for full_key, ent in self.entries.items():
            section, key = full_key.split('.')
            val = ent.get().strip()
            if section == 'tunnel' and key in ('local_port', 'remote_port'):
                try:
                    val = int(val)
                except ValueError:
                    messagebox.showerror("Ошибка",
                                         f"Поле «{key}» должно быть числом.",
                                         parent=self)
                    return
            cfg.setdefault(section, {})[key] = val

        # Чтение и валидация памяти
        try:
            mn = int(self.min_mem_var.get())
            mx = int(self.max_mem_var.get())
        except ValueError:
            messagebox.showerror("Ошибка",
                                 "Поля памяти должны быть целыми числами.",
                                 parent=self)
            return
        if mn > mx:
            messagebox.showerror("Ошибка",
                                 "Минимум памяти не может быть больше максимума.",
                                 parent=self)
            return
        # Собираем mem_opts
        cfg.setdefault('server', {})['mem_opts'] = f"-Xms{mn}M -Xmx{mx}M"

        # Сохраняем
        self.on_save(cfg)
        messagebox.showinfo("Настройки",
                            "Настройки сохранены.\nПерезапустите приложение для применения.",
                            parent=self)
        self.destroy()

class AppGUI:
    def __init__(self, config):
        self.config = config
        self.root   = tk.Tk()
        self.root.title("Minecraft Server Manager")
        self.root.geometry("900x600")

        self.console = scrolledtext.ScrolledText(self.root, state='disabled', height=25)
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.server_status = tk.Label(self.root, text="Сервер: не запущен", fg="goldenrod")
        self.server_status.pack(pady=2)
        self.ssh_status    = tk.Label(self.root, text="SSH-туннель: не запущен", fg="goldenrod")
        self.ssh_status.pack(pady=2)

        self.server_starting = False
        self.server_stopping = False
        self.tunnel_starting = False
        self.tunnel_stopping = False
        self.server_ready    = False

        tcfg  = config['tunnel']
        scfg  = config['server']
        paths = config['paths']

        self.server = ServerManager(
            server_dir=paths['server_files'],
            jar_file=scfg['jar_file'],
            mem_opts=scfg['mem_opts'],
            console_append=self._on_server_output,
            on_ready=self._on_server_ready
        )
        self.tunnel = TunnelManager(
            user=tcfg['user'], host=tcfg['host'],
            local_port=tcfg['local_port'], remote_port=tcfg['remote_port'],
            console_append=self._on_tunnel_output
        )

        self._create_buttons()
        threading.Thread(target=self._monitor_statuses, daemon=True).start()

    def _on_server_output(self, text):
        self.console_insert(text)
        if "Запуск сервера" in text:
            self.server_starting = False
        if "Сервер остановлен" in text:
            self.server_stopping = False
            self.server_ready = False
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
            ("Start Server",   self._start_server),
            ("Stop Server",    self._stop_server),
            ("Start Tunnel",   self._start_tunnel),
            ("Stop Tunnel",    self._stop_tunnel),
            ("Restart Server", self._restart_server),
            ("New World",      lambda: self.server.restart_with_new_world(
                                  self.config['paths']['backups'])),
            ("Settings",       self._open_settings),
            ("Help",           self._show_help),
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
            "New World      – перезапустить с новым миром (архивация из server_files/world)\n"
        )
        messagebox.showinfo("Help", msg)

    def _open_settings(self):
        SettingsWindow(self.root, self.config, ConfigManager.save_config)

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