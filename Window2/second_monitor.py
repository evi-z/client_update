import os
import subprocess
import sys
import time

PathFile = os.path.abspath(__file__)
ROOT_PATH = PathFile.replace(r'\second_monitor.py', '').strip()

subprocess.call(ROOT_PATH + r'\second_monitor.pyw', shell=True)
time.sleep(1)
sys.exit()

