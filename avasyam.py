import wmi
import psutil
import platform
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
from datetime import datetime
import winreg
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os

def get_wmi(namespace=None):
    return wmi.WMI(namespace=namespace) if namespace else wmi.WMI()

# ------------- USB HISTORY MODULE -------------
def get_pendrives_from_registry():
    usb_devices = []
    reg_path = r"SYSTEM\\CurrentControlSet\\Enum\\USBSTOR"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
            for i in range(winreg.QueryInfoKey(key)[0]):
                device_key_name = winreg.EnumKey(key, i)
                device_path = f"{reg_path}\\{device_key_name}"
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, device_path) as device_key:
                    for j in range(winreg.QueryInfoKey(device_key)[0]):
                        instance_key_name = winreg.EnumKey(device_key, j)
                        instance_path = f"{device_path}\\{instance_key_name}"
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, instance_path) as instance_key:
                            try:
                                friendly_name, _ = winreg.QueryValueEx(instance_key, "FriendlyName")
                            except:
                                friendly_name = "Unknown Device"
                            if any(x in friendly_name.lower() for x in ["usb", "cruzer", "storage", "mass storage", "pendrive", "flash"]):
                                usb_devices.append({
                                    "Device Name": friendly_name,
                                    "Serial": instance_key_name
                                })
    except Exception as e:
        usb_devices.append({"Device Name": f"Error accessing registry: {e}", "Serial": "N/A"})
    return usb_devices

def save_usb_history_pdf():
    devices = get_pendrives_from_registry()
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(base_path, f"AVASYAM_USB_History_{now}.pdf")

    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>AVASYAM USB Pendrive History Report</b>", styles['Title']))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    if devices:
        for idx, d in enumerate(devices, 1):
            elements.append(Paragraph(f"{idx}. Device Name: {d['Device Name']}", styles['Normal']))
            elements.append(Paragraph(f"Serial: {d['Serial']}", styles['Normal']))
            elements.append(Spacer(1, 6))
    else:
        elements.append(Paragraph("No pendrives found in registry history.", styles['Normal']))

    doc.build(elements)
    os.startfile(filename)
    messagebox.showinfo("AVASYAM", f"✅ USB History PDF saved and opened:\n{filename}")

# ------------- REST OF YOUR AVASYAM FUNCTIONS -------------

def check_antivirus():
    try:
        security_wmi = get_wmi(namespace="root\\SecurityCenter2")
        antivirus_products = security_wmi.InstancesOf("AntiVirusProduct")
        return (4, "Antivirus Detected") if antivirus_products else (0, "No Antivirus Detected")
    except:
        return 0, "Error Checking Antivirus"

def check_firewall():
    try:
        result = subprocess.run(['powershell', '-Command', 'Get-NetFirewallProfile | Select-Object Enabled'], capture_output=True, text=True)
        enabled_count = result.stdout.lower().count("true")
        if enabled_count == 3:
            return 3, "All Profiles Active"
        elif enabled_count == 2:
            return 2, "Two Profiles Active"
        elif enabled_count == 1:
            return 1, "One Profile Active"
        else:
            return 0, "Firewall Disabled"
    except:
        return 0, "Error Checking Firewall"

def check_established_connections():
    try:
        count = len([c for c in psutil.net_connections(kind='tcp') if c.status == 'ESTABLISHED'])
        if count == 0:
            return 2, "0 Established Connections"
        elif count <= 5:
            return 1, f"{count} Established Connections"
        else:
            return 0, f"{count} Established Connections"
    except:
        return 0, "Error Checking Connections"

def check_udp_connections():
    try:
        count = len(psutil.net_connections(kind='udp'))
        if count == 0:
            return 3, "0 UDP Connections"
        elif count <= 15:
            return 2, f"{count} UDP Connections"
        elif count <= 30:
            return 1, f"{count} UDP Connections"
        else:
            return 0, f"{count} UDP Connections"
    except:
        return 0, "Error Checking UDP"

def check_password_strength():
    return 3, "Strong (Assumed for Lab)"

def check_windows_version():
    try:
        build_number = int(platform.version().split('.')[2])
        if build_number >= 22000:
            return 4, f"Windows 11 (Build {build_number})"
        elif 10240 <= build_number < 22000:
            return 1, f"Windows 10 (Build {build_number})"
        elif 9200 <= build_number < 10240:
            return 1, f"Windows 8/8.1 (Build {build_number})"
        elif 7600 <= build_number < 9200:
            return 0, f"Windows 7 (Build {build_number})"
        elif build_number < 7600:
            return -5, f"Windows XP or Older (Build {build_number})"
        else:
            return 0, f"Unknown Windows Version (Build {build_number})"
    except Exception as e:
        return 0, f"Error Checking OS: {e}"

def check_usb():
    try:
        usb_count = len([d for d in get_wmi().Win32_DiskDrive() if d.InterfaceType == "USB"])
        if usb_count == 0:
            return 3, "No USB Plugged"
        elif usb_count <= 5:
            return 2, f"{usb_count} USB(s) Plugged"
        else:
            return 0, f"{usb_count} USB(s) Plugged"
    except:
        return 0, "Error Checking USB"

def check_extra_programs():
    try:
        count = len(list(get_wmi().Win32_Product()))
        if count <= 10:
            return 2, f"{count} Programs"
        elif count <= 20:
            return 1, f"{count} Programs"
        else:
            return 0, f"{count} Programs"
    except:
        return 0, "Error Checking Programs"

def check_rdp_ports():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\\CurrentControlSet\\Control\\Terminal Server")
        value, _ = winreg.QueryValueEx(key, "fDenyTSConnections")
        return (1, "RDP Off") if value == 1 else (0, "RDP On")
    except:
        return 0, "Error Checking RDP"

def check_shared_folders():
    try:
        count = len(get_wmi().Win32_Share())
        if count == 0:
            return 2, "No Shared Folders"
        elif count <= 3:
            return 1, f"{count} Shared Folders"
        else:
            return 0, f"{count} Shared Folders"
    except:
        return 0, "Error Checking Shares"

def check_unwanted_software():
    try:
        count = len(list(get_wmi().Win32_Product()))
        if count <= 10:
            return 3, "No Unwanted Software (Assumed)"
        elif count <= 13:
            return 2, "1-3 Unwanted Software (Assumed)"
        elif count <= 16:
            return 1, "4-6 Unwanted Software (Assumed)"
        else:
            return 0, "7+ Unwanted Software (Assumed)"
    except:
        return 0, "Error Checking Unwanted Software"

def check_open_ports():
    try:
        unusual_ports = [c.laddr.port for c in psutil.net_connections(kind='inet') if c.status == 'LISTEN' and c.laddr.port not in [80, 443, 135, 445, 3389]]
        count = len(set(unusual_ports))
        if count <= 3:
            return 2, f"{count} Unusual Ports"
        elif count <= 6:
            return 1, f"{count} Unusual Ports"
        else:
            return 0, f"{count} Unusual Ports"
    except:
        return 0, "Error Checking Ports"

def save_pdf(results, level, percentage):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(base_path, f"AVASYAM_Report_{now}.pdf")
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph("<b>AVASYAM Automated Security Audit Report</b>", styles['Title']))
    elements.append(Paragraph(f"<b>Date & Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph(f"<b>Security Level:</b> {level} ({percentage}%)", styles['Heading2']))
    elements.append(Spacer(1, 20))
    data = [["Parameter", "Detail", "Score"]]
    for row in results:
        data.append(list(row))
    table = Table(data, colWidths=[150, 250, 100])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ])
    table.setStyle(style)
    for i in range(1, len(data)):
        score = str(data[i][2])
        if score.isdigit():
            score_value = int(score)
            bg_color = colors.lightgreen if score_value > 2 else colors.lightyellow if score_value > 0 else colors.lightcoral
            table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), bg_color)]))
    elements.append(table)
    doc.build(elements)
    os.startfile(filename)
    messagebox.showinfo("AVASYAM", f"✅ PDF saved and opened:\n{filename}")

def run_audit():
    results = []
    total_score = 0
    checks = [
        ("Antivirus", check_antivirus),
        ("Firewall", check_firewall),
        ("Established Connections", check_established_connections),
        ("UDP Connections", check_udp_connections),
        ("Password Strength", check_password_strength),
        ("Windows Version", check_windows_version),
        ("USB Plugged", check_usb),
        ("Extra Programs", check_extra_programs),
        ("RDP Ports", check_rdp_ports),
        ("Shared Folders", check_shared_folders),
        ("Unwanted Software", check_unwanted_software),
        ("Open Ports", check_open_ports),
    ]
    for label, func in checks:
        score, detail = func()
        total_score += score
        results.append((label, detail, str(score)))
    max_score = 30
    percentage = max(0, min(100, round((total_score / max_score) * 100)))
    level = "Low Security" if percentage <= 33 else "Medium Security" if percentage <= 66 else "High Security"
    results.append(("Total Score", f"{total_score}/{max_score}", str(percentage)))
    results.append(("Security Level", level, ""))
    update_table(results)
    save_pdf(results, level, percentage)

def update_table(results):
    for item in tree.get_children():
        tree.delete(item)
    for row in results:
        tree.insert("", "end", values=row)

# GUI
root = tk.Tk()
root.title("AVASYAM Automated Security Audit Tool (with USB History)")
root.geometry("750x550")
root.resizable(False, False)
tk.Label(root, text="AVASYAM Automated Security Audit", font=("Segoe UI", 18)).pack(pady=10)
tk.Button(root, text="Run Security Audit", font=("Segoe UI", 14), bg="#1e3a8a", fg="white", command=run_audit).pack(pady=5)
tk.Button(root, text="Generate USB History Report", font=("Segoe UI", 14), bg="#1e3a8a", fg="white", command=save_usb_history_pdf).pack(pady=5)
columns = ("Parameter", "Detail", "Score")
tree = ttk.Treeview(root, columns=columns, show="headings", height=15)
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=240)
tree.pack(pady=10, fill="both", expand=True)
root.mainloop()
