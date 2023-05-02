import time
import subprocess

arguments = ["sudo", "bluetoothctl"]
output = subprocess.Popen(arguments, shell=True)
time.sleep(0.1)
arguments = ["agent", "on"]
output = subprocess.Popen(arguments, shell=True)
time.sleep(0.1)
arguments = ["scan", "on"]
output = subprocess.check_output(arguments, shell=True)
time.sleep(0.1)

print(output)