#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from mcmanager.gui import AppGUI

load_dotenv()

config = {
    'tunnel': {
        'user':       os.getenv('SSH_USER'),
        'host':       os.getenv('SSH_HOST'),
        'local_port': int(os.getenv('LOCAL_PORT', '25565')),
        'remote_port':int(os.getenv('REMOTE_PORT', '25565')),
    },
    'server': {
        'jar_file': os.getenv('JAR_FILE', 'paper.jar'),
        'mem_opts':  os.getenv('MEM_OPTS', '-Xms512M -Xmx2G'),
    },
    'paths': {
        'world':   os.getenv('WORLD_DIR', 'world'),
        'backups': os.getenv('ARCHIVE_DIR', 'world_backups'),
    }
}

if __name__ == "__main__":
    AppGUI(config).run()
