import subprocess

ADB = r"C:\Users\Chirag\Desktop\btp\eid\platform-tools-latest-windows\platform-tools\adb.exe"

def get_imei():
    try:
        out = subprocess.check_output(
            [ADB, "shell", "service", "call", "iphonesubinfo", "1"]
        ).decode("utf-8", errors="ignore")

        digits = "".join(c for c in out if c.isdigit())
        return digits[:15] if len(digits) >= 15 else "Not Found"

    except subprocess.CalledProcessError:
        return "Error"

print(get_imei())