import subprocess
import tkinter as tk
from tkinter import ttk

ADB = r"C:\Users\Chirag\Desktop\btp\eid\platform-tools-latest-windows\platform-tools\adb.exe"

# ---------- HELPERS ----------

def adb(cmd):
    try:
        return subprocess.check_output(cmd, shell=True).decode().strip()
    except:
        return ""

# ---------- FETCH FUNCTIONS ----------

def get_eid():
    # Try multiple sources
    eid = adb(f"{ADB} shell getprop gsm.sim.eid")
    if len(eid) > 10:
        return eid

    eid = adb(f"{ADB} shell getprop persist.radio.eid")
    if len(eid) > 10:
        return eid

    data = adb(f"{ADB} shell dumpsys isub")
    for line in data.split("\n"):
        if "eid" in line.lower():
            return line.split("=")[-1].strip()

    return "Not Found"


def get_serial():
    return adb(f"{ADB} get-serialno")


def get_imei():
    out = adb(f"{ADB} shell service call iphonesubinfo 1")
    digits = "".join([c for c in out if c.isdigit()])
    return digits[:15] if len(digits) >= 15 else "Not Found"


# ---------- GUI ----------

root = tk.Tk()
root.title("Verification Tool")
root.geometry("750x550")
root.configure(bg="#7fa2bd")

# Inputs
eid_in = tk.StringVar()
sn_in = tk.StringVar()
imei_in = tk.StringVar()

# Device values
eid_dev = tk.StringVar(value="---")
sn_dev = tk.StringVar(value="---")
imei_dev = tk.StringVar(value="---")

# Result
result_var = tk.StringVar(value="PASS/FAIL")

# ---------- UI ----------

tk.Label(root, text="verification tool", font=("Segoe UI", 22),
         bg="#7fa2bd", fg="white").pack(pady=20)

frame = tk.Frame(root, bg="#7fa2bd")
frame.pack()

def row(r, text, var_in, var_dev):
    tk.Label(frame, text=text, font=("Segoe UI", 14),
             bg="#7fa2bd").grid(row=r, column=0, padx=10, pady=10)

    tk.Entry(frame, textvariable=var_in, width=25,
             font=("Segoe UI", 13)).grid(row=r, column=1)

    tk.Label(frame, textvariable=var_dev,
             font=("Segoe UI", 13),
             bg="#7fa2bd").grid(row=r, column=2)

eid_row = row(0, "Scan box EID :", eid_in, eid_dev)
sn_row = row(1, "Scan box S/N :", sn_in, sn_dev)
imei_row = row(2, "Scan box IMEI :", imei_in, imei_dev)

# ---------- LOGIC ----------

def compare():
    eid = get_eid()
    sn = get_serial()
    imei = get_imei()

    eid_dev.set(eid)
    sn_dev.set(sn)
    imei_dev.set(imei)

    # FINAL LOGIC: ALL MUST MATCH
    if (eid == eid_in.get().strip() and
        sn == sn_in.get().strip() and
        imei == imei_in.get().strip()):
        
        result_var.set("PASS")
        result_label.config(fg="green")
    else:
        result_var.set("FAIL")
        result_label.config(fg="red")


def clear():
    eid_in.set("")
    sn_in.set("")
    imei_in.set("")
    eid_dev.set("---")
    sn_dev.set("---")
    imei_dev.set("---")
    result_var.set("PASS/FAIL")

# ---------- BUTTONS ----------

btn_frame = tk.Frame(root, bg="#7fa2bd")
btn_frame.pack(pady=20)

tk.Button(btn_frame, text="Fetch & Compare",
          bg="#7ed957", font=("Segoe UI", 14),
          command=compare).grid(row=0, column=0, padx=20)

tk.Button(btn_frame, text="Clear",
          bg="lightgray", font=("Segoe UI", 14),
          command=clear).grid(row=0, column=1)

# ---------- RESULT ----------

result_label = tk.Label(root, textvariable=result_var,
                        font=("Segoe UI", 30),
                        bg="#7fa2bd")
result_label.pack(pady=20)

# ---------- TABLE ----------

tree = ttk.Treeview(root, columns=("Key", "Value"), show="headings")
tree.heading("Key", text="Property")
tree.heading("Value", text="Value")
tree.pack(fill="both", expand=True, padx=10, pady=10)

def load_info():
    tree.delete(*tree.get_children())
    data = [
        ("Serial", get_serial()),
        ("Model", adb(f"{ADB} shell getprop ro.product.model")),
        ("Brand", adb(f"{ADB} shell getprop ro.product.brand")),
    ]
    for d in data:
        tree.insert("", "end", values=d)

tk.Button(root, text="Get Info", command=load_info).pack(pady=10)

root.mainloop()