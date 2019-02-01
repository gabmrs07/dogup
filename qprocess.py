#!/usr/bin/env python

import subprocess
from sys import argv

log_tray_path = argv[1]

subprocess.run(f'sudo pacman -Su --noconfirm &>> {log_tray_path}', shell = True)
