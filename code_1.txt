import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

# --------- Fetch IMEI via ADB ----------
def get_imei():
    try:
        # Try method 1 (common in factory devices)
        output = subprocess.check_output(
            ["adb", "shell", "service", "call", "iphonesubinfo", "1"],
            stderr=subprocess.STDOUT
        ).decode()

        imei = "".join([c for c in output if c.isdigit()])
        if len(imei) >= 14:
            return imei

        # Try method 2 (fallback)
        output2 = subprocess.check_output(
            ["adb", "shell", "getprop"],
            stderr=subprocess.STDOUT
        ).decode()

        for line in output2.split("\n"):
            if "imei" in line.lower():
                val = line.split("]: [")[-1].replace("]", "").strip()
                if val:
                    return val

        return "IMEI Not Found"

    except Exception as e:
        return "ADB Error"

# --------- Compare ----------
def compare_imei():
    box_imei = entry_box.get().strip()

    if not box_imei:
        messagebox.showwarning("Input Error", "Enter Box IMEI")
        return

    phone_imei = get_imei()
    label_phone_value.config(text=phone_imei)

    if phone_imei in ["ADB Error", "IMEI Not Found"]:
        result_label.config(text="❌ Unable to fetch IMEI", foreground="red")
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

# --------- GUI ----------
root = tk.Tk()
root.title("IMEI Verification System")
root.geometry("500x350")

title = ttk.Label(root, text="IMEI Verification Tool", font=("Segoe UI", 16, "bold"))
title.pack(pady=15)

frame = ttk.Frame(root, padding=20)
frame.pack()

ttk.Label(frame, text="Enter Box IMEI:").grid(row=0, column=0, pady=5)
entry_box = ttk.Entry(frame, width=40)
entry_box.grid(row=0, column=1, pady=5)

ttk.Label(frame, text="Phone IMEI:").grid(row=1, column=0, pady=5)
label_phone_value = ttk.Label(frame, text="---", foreground="blue")
label_phone_value.grid(row=1, column=1, pady=5)

btn_frame = ttk.Frame(frame)
btn_frame.grid(row=2, column=0, columnspan=2, pady=15)

ttk.Button(btn_frame, text="Fetch & Compare", command=compare_imei).grid(row=0, column=0, padx=10)
ttk.Button(btn_frame, text="Clear", command=clear_fields).grid(row=0, column=1, padx=10)

result_label = ttk.Label(root, text="", font=("Segoe UI", 14, "bold"))
result_label.pack(pady=20)

root.mainloop()