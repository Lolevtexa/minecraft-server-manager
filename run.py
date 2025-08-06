from mcmanager.config_manager import ConfigManager
from mcmanager.gui import AppGUI

if __name__ == "__main__":
    config = ConfigManager.load_config()
    AppGUI(config).run()