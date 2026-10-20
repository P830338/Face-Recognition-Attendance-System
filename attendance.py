import cv2
import pandas as pd
import os
from datetime import datetime
from deepface import DeepFace
import pyttsx3
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Text to speech engine
engine = pyttsx3.init()

# Known faces folder
photos_path = "photos"
attendance_list = []

# ========== GUI SETUP ==========
root = tk.Tk()
root.title("Face Recognition Attendance System")
root.geometry("900x600")
root.configure(bg="#2c3e50")

# Title
title = tk.Label(root, text="Face Recognition Attendance System",
                 font=("Arial", 16, "bold"), bg="#2c3e50", fg="white")
title.pack(pady=10)

# Subject Entry
subject_frame = tk.Frame(root, bg="#2c3e50")
subject_frame.pack(pady=5)
tk.Label(subject_frame, text="Subject:", bg="#2c3e50", fg="white", font=("Arial", 12)).pack(side="left")
subject_entry = tk.Entry(subject_frame, font=("Arial", 12), width=20)
subject_entry.pack(side="left", padx=10)

# Status Label
status_label = tk.Label(root, text="Status: Ready", font=("Arial", 12),
                        bg="#2c3e50", fg="#2ecc71")
status_label.pack(pady=5)

# Attendance Table
columns = ("Name", "Subject", "Date", "Time", "Status")
tree = ttk.Treeview(root, columns=columns, show="headings", height=10)
tree.column("Name", width=150)
tree.column("Subject", width=150)
tree.column("Date", width=120)
tree.column("Time", width=100)
tree.column("Status", width=80)
for col in columns:
    tree.heading(col, text=col)
tree.pack(pady=10)

# Buttons Frame
btn_frame = tk.Frame(root, bg="#2c3e50")
btn_frame.pack(pady=10)

# ========== FUNCTIONS ==========
def mark_attendance(name, subject):
    key = f"{name}_{subject}"
    if key not in attendance_list:
        attendance_list.append(key)
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")

        hour = now.hour
        status = "Late" if hour >= 10 else "Present"

        tree.insert("", "end", values=(name, subject, date, time, status))

    def speak(text):
        tts = pyttsx3.init()
        tts.say(text)
        tts.runAndWait()

        threading.Thread(target=speak, args=(f"Attendance marked for {name}",), daemon=True).start()

        status_label.config(text=f"Status: {name} - {status}!", fg="#2ecc71")
        print(f"Attendance marked: {name} | {subject} | {status}")

def save_attendance():
    if not attendance_list:
        messagebox.showwarning("Warning", "No attendance to save!")
        return

    rows = []
    for item in tree.get_children():
        rows.append(tree.item(item)["values"])

    df = pd.DataFrame(rows, columns=["Name", "Subject", "Date", "Time", "Status"])
    filename = f"attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    messagebox.showinfo("Saved!", f"Attendance saved to {filename}")

running = False

def start_camera():
    global running
    running = True
    start_btn.config(state="disabled")
    stop_btn.config(state="normal")
    threading.Thread(target=run_camera, daemon=True).start()

def stop_camera():
    global running
    running = False
    start_btn.config(state="normal")
    stop_btn.config(state="disabled")
    status_label.config(text="Status: Camera Stopped", fg="#e74c3c")

def run_camera():
    subject = subject_entry.get() or "General"
    video_capture = cv2.VideoCapture(0)

    frame_count = 0
    while running:
        ret, frame = video_capture.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % 30 != 0:
            cv2.imshow("Camera", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        cv2.imwrite("temp_frame.jpg", frame)

        face_found = False
        for filename in os.listdir(photos_path):
            if filename.endswith((".jpg", ".jpeg", ".png")):
                name = os.path.splitext(filename)[0]
                try:
                    result = DeepFace.verify("temp_frame.jpg",
                                             f"{photos_path}/{filename}",
                                             enforce_detection=True,
                                             silent=True)
                    if result["verified"]:
                        face_found = True
                        root.after(0, mark_attendance, name, subject)
                except:
                    pass

        if not face_found:
            cv2.putText(frame, "Unknown / No Face", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            root.after(0, lambda: status_label.config(
                text="Status: Unknown Face!", fg="#e74c3c"))

        cv2.imshow("Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    if os.path.exists("temp_frame.jpg"):
        os.remove("temp_frame.jpg")

# Buttons
start_btn = tk.Button(btn_frame, text="Start Camera", command=start_camera,
                      bg="#2ecc71", fg="white", font=("Arial", 12), width=15)
start_btn.pack(side="left", padx=10)

stop_btn = tk.Button(btn_frame, text="Stop Camera", command=stop_camera,
                     bg="#e74c3c", fg="white", font=("Arial", 12), width=15, state="disabled")
stop_btn.pack(side="left", padx=10)

save_btn = tk.Button(btn_frame, text="Save Attendance", command=save_attendance,
                     bg="#3498db", fg="white", font=("Arial", 12), width=15)
save_btn.pack(side="left", padx=10)

root.mainloop()