import time
import subprocess
import easyocr
from PIL import Image

# ---- STEP 1: Open About Phone ----
ADB = r"C:\Users\Chirag\Desktop\btp\eid\platform-tools-latest-windows\platform-tools\adb.exe"

subprocess.call([ADB, "shell", "am", "start", "-a", "android.settings.DEVICE_INFO_SETTINGS"])
time.sleep(3)

# ---- Scroll down (adjust if needed) ----
subprocess.call([ADB, "shell", "input", "swipe", "500", "1500", "500", "500"])
time.sleep(2)

# ---- Tap "Status info" (coordinates needed) ----
subprocess.call([ADB, "shell", "input", "tap", "400", "1000"])
time.sleep(3)

# ---- Take Screenshot ----
subprocess.call([ADB, "shell", "screencap", "/sdcard/screen.png"])
subprocess.call([ADB, "pull", "/sdcard/screen.png"])

# ---- STEP 3: OCR Read ----
reader = easyocr.Reader(['en'])
result = reader.readtext('stats.jpeg')

phone_eid = result[6][1]


# ---- STEP 5: Compare ----
box_eid = input("Enter Box EID: ")

print("Phone EID:", phone_eid)

if phone_eid == box_eid:
    print("PASS")
else:
    print("FAIL")