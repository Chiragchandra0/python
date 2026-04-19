import time
from ppadb.client import Client

client = Client(host="127.0.0.1", port=5037)
devices = client.devices()
device = devices[0]

# Tap to open dial pad (your coordinates)
device.shell('input tap 110 2200')
time.sleep(3)

device.shell('input tap 110 2200')
time.sleep(3)
# Type *#06#
device.shell('input keyevent KEYCODE_STAR')
time.sleep(0.2)

device.shell('input keyevent KEYCODE_POUND')
time.sleep(0.2)

device.shell('input keyevent KEYCODE_0')
time.sleep(0.2)

device.shell('input keyevent KEYCODE_6')
time.sleep(0.2)

device.shell('input keyevent KEYCODE_POUND')