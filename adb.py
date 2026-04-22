import subprocess
import time
import tkinter as tk
from tkinter import ttk, messagebox
import easyocr

ADB = r"C:\Users\Chirag\Desktop\btp\eid\platform-tools-latest-windows\platform-tools\adb.exe"

# --------- Fetch IMEI via ADB + OCR ----------
def get_imei():
    subprocess.call([ADB, "shell", "am", "start", "-a", "android.settings.DEVICE_INFO_SETTINGS"])
    time.sleep(3)

    subprocess.call([ADB, "shell", "input", "swipe", "500", "1500", "500", "500"])
    time.sleep(2)

    subprocess.call([ADB, "shell", "input", "tap", "400", "1000"])
    time.sleep(3)

    subprocess.call([ADB, "shell", "screencap", "/sdcard/screen.png"])
    subprocess.call([ADB, "pull", "/sdcard/screen.png"])

    reader = easyocr.Reader(['en'])
    result = reader.readtext('screen.png')

    for item in result:
        text = item[1]
        if text.isdigit() and len(text) > 14:
            return text

    return "Not Found"

# --------- Compare ----------
def compare_imei():
    box_imei = entry_box.get().strip()

    if not box_imei:
        messagebox.showwarning("Input Error", "Enter Box IMEI")
        return

    phone_imei = get_imei()
    label_phone_value.config(text=phone_imei)

    if phone_imei == "Not Found":
        result_label.config(text="❌ Unable to fetch", foreground="red")
        return

    if box_imei == phone_imei:
        result_label.config(text="✅ PASS", foreground="green")
    else:
        result_label.config(text="❌ FAIL", foreground="red")

# --------- Clear ----------
def clear_fields():
    entry_box.delete(0, tk.END)
    label_phone_value.config(text="---")
    result_label.config(text="")

# --------- Load Device Info (same window) ----------
def load_device_info():
    tree.delete(*tree.get_children())

    try:
        output = subprocess.check_output([ADB, "shell", "getprop"]).decode()

        for line in output.split("\n"):
            if "model" in line.lower():
                tree.insert("", "end", values=("Model", line.split("]: [")[-1].replace("]", "")))
            elif "version.release" in line.lower():
                tree.insert("", "end", values=("Android Version", line.split("]: [")[-1].replace("]", "")))
            elif "brand" in line.lower():
                tree.insert("", "end", values=("Brand", line.split("]: [")[-1].replace("]", "")))

    except:
        tree.insert("", "end", values=("Error", "Device not connected"))

# --------- GUI ----------
root = tk.Tk()
root.title("IMEI Verification System")
root.geometry("550x500")

# --------- MENU ----------
menu_bar = tk.Menu(root)

file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Compare", command=lambda: None)
file_menu.add_command(label="Device Info", command=load_device_info)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

menu_bar.add_cascade(label="File", menu=file_menu)
root.config(menu=menu_bar)

# --------- UI ----------
title = ttk.Label(root, text="IMEI Verification Tool", font=("Segoe UI", 16, "bold"))
title.pack(pady=10)

frame = ttk.Frame(root, padding=15)
frame.pack()

ttk.Label(frame, text="Enter Box IMEI:").grid(row=0, column=0, pady=5)
entry_box = ttk.Entry(frame, width=35)
entry_box.grid(row=0, column=1, pady=5)

ttk.Label(frame, text="Phone IMEI:").grid(row=1, column=0, pady=5)
label_phone_value = ttk.Label(frame, text="---", foreground="blue")
label_phone_value.grid(row=1, column=1, pady=5)

btn_frame = ttk.Frame(frame)
btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

ttk.Button(btn_frame, text="Fetch & Compare", command=compare_imei).grid(row=0, column=0, padx=10)
ttk.Button(btn_frame, text="Clear", command=clear_fields).grid(row=0, column=1, padx=10)

result_label = ttk.Label(root, text="", font=("Segoe UI", 14, "bold"))
result_label.pack(pady=10)

# --------- Device Info Table (same window) ----------
table_frame = ttk.Frame(root)
table_frame.pack(fill="both", expand=True, padx=10, pady=10)

tree = ttk.Treeview(table_frame, columns=("Key", "Value"), show="headings", height=6)
tree.heading("Key", text="Property")
tree.heading("Value", text="Value")
tree.pack(fill="both", expand=True)

root.mainloop()