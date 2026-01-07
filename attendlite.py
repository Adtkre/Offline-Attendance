# --------------------------
# AttendLite.py (UPDATED)
# --------------------------

import qrcode
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import os
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string
import threading
import socket
import csv

downloads_path = str(Path.home() / "Downloads")
ATTENDANCE_FILE = os.path.join(downloads_path, "attendance.csv")
STUDENT_PAGE_FILE = "student_page.html" 

# Initialize the CSV file safely
if not os.path.exists(ATTENDANCE_FILE):
    try:
        # Initialize the file with headers using the standard csv module
        with open(ATTENDANCE_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Student Name", "Roll Number", "Lecture ID", "Timestamp"])
        print(f"Created new attendance file at: {ATTENDANCE_FILE}")
    except Exception as e:
        print(f"Could not create initial CSV file: {e}")


app = Flask(__name__)

# Serve student page
@app.route("/lecture/<lecture_id>")
def lecture_page(lecture_id):
    try:
        # Note: You need to create a file named 'student_page.html'
        with open(STUDENT_PAGE_FILE, 'r') as f:
            template = f.read()
        return render_template_string(template, lecture_id=lecture_id)
    except FileNotFoundError:
        return f"Error: Student page template ({STUDENT_PAGE_FILE}) not found.", 500

# Receive submission 
@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    student_name = data.get("student_name")
    roll_number = data.get("roll_number")
    lecture_id = data.get("lecture_id")
    timestamp = data.get("timestamp") 

    if not all([student_name, roll_number, lecture_id, timestamp]):
        return jsonify({"status":"error","message":"Incomplete data"}), 400

    try:
        
        with open(ATTENDANCE_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            writer.writerow([student_name, roll_number, lecture_id, timestamp])
            
        return jsonify({"status":"success"})
    except Exception as e:
        print(f"Error saving data: {e}")
        return jsonify({"status":"error", "message": "Server failed to save attendance"}), 500


def run_flask():
    
    print("Starting Flask server...")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

#GUI-PROFESSOR
root = tk.Tk()
root.title("AttendLite - Offline-First QR Attendance")
root.geometry("500x650")


tk.Label(root, text="Lecture Name:").pack(pady=(10, 0)) 
lecture_entry = tk.Entry(root, width=30)
lecture_entry.pack(pady=5)

lecture_id_label = tk.Label(root, text="")
lecture_id_label.pack()

qr_label = tk.Label(root)
qr_label.pack(pady=10)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        
        s.connect(("8.8.8.8", 80)) 
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP

def generate_qr():
    lecture = lecture_entry.get()
    if not lecture:
        messagebox.showwarning("Input Required", "Please enter Lecture Name")
        return

    # Create a simple slug for the lecture ID
    lecture_slug = lecture.replace(" ", "_").strip()
    lecture_id = f"{lecture_slug}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    local_ip = get_local_ip()
    url = f"http://{local_ip}:5000/lecture/{lecture_id}"

    # Generate QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img.save("current_qr.png")

    qr_img = Image.open("current_qr.png")
    qr_img = qr_img.resize((300,300))
    tk_img = ImageTk.PhotoImage(qr_img)
    
    # Update QR image and metadata
    qr_label.config(image=tk_img)
    qr_label.image = tk_img 

    lecture_id_label.config(text=f"Lecture ID: {lecture_id}\nURL: {url}")
    messagebox.showinfo("QR Generated", f"Lecture ID: {lecture_id}\nURL: {url}\n\nStudents can scan with camera. Offline submissions auto-sync when internet is back.")

def export_csv():
    # Simply informs the professor where the file is located (since it updates automatically)
    if os.path.exists(ATTENDANCE_FILE):
        messagebox.showinfo("Attendance Location", f"Attendance is being automatically saved/updated at:\n\n{ATTENDANCE_FILE}\n\nJust open this CSV to see the latest data.")
    else:
        messagebox.showwarning("No Data", "No attendance data found.")

tk.Button(root, text="Generate QR", command=generate_qr).pack(pady=10)
tk.Button(root, text="Show CSV Location", command=export_csv).pack(pady=20)

root.mainloop()