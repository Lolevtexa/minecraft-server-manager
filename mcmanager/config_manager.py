import json
import os

DEFAULT_CONFIG = {
    "tunnel": {
        "user": "",
        "host": "",
        "local_port": 25565,
        "remote_port": 25565
    },
    "server": {
        "jar_file": "paper.jar",
        "mem_opts": "-Xms512M -Xmx2G"
    },
    "paths": {
        "server_files": "server_files",
        "backups":      "world_backups"
    }
}

class ConfigManager:
    CONFIG_FILE = "config.json"

    @staticmethod
    def load_config():
        """
        Если нет config.json — создаём его из стандартных значений.
        Иначе — читаем и возвращаем.
        """
        if not os.path.exists(ConfigManager.CONFIG_FILE):
            with open(ConfigManager.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
            return DEFAULT_CONFIG.copy()

        with open(ConfigManager.CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_config(config: dict):
        """
        Перезаписываем config.json новыми значениями.
        """
        with open(ConfigManager.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)