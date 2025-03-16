import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
import datetime
import cv2
import numpy as np
import logging
from database import connect_to_mongodb, hash_password, save_user_data, register_user, authenticate_user
from emotion_model import load_emotion_model, load_face_cascade, detect_faces, preprocess_face, predict_emotion
from stress_analysis import calculate_stress_level, get_recommendation
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Global Variables
webcam_running = False
current_user = None
cap = None  # Webcam VideoCapture Object
daily_routine = ""  # Store daily routine entered by user

# Load Emotion Model and Face Cascade
emotion_labels = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]
model_path = r"D:\PROJECT\PRJCT\emotion_model.h5"
emotion_model = load_emotion_model(model_path)
face_cascade = load_face_cascade()

# MongoDB Connection
collection, user_collection = connect_to_mongodb()

# Create the GUI
def create_gui(root):
    # Set a modern theme with a darker background
    root.configure(bg="#2c3e50")  # Dark blue background
    root.geometry("1200x800")  # Larger window size
    root.title("Stress Level Management System")

    # Custom fonts
    title_font = ("Helvetica", 24, "bold")
    button_font = ("Helvetica", 14)
    label_font = ("Helvetica", 12)

    # Webcam Feed Handler
    def start_webcam():
        global webcam_running, cap
        webcam_running = True
        cap = cv2.VideoCapture(0)
        show_frame()

    def stop_webcam():
        global webcam_running, cap
        webcam_running = False
        if cap:
            cap.release()
        webcam_label.config(image='')

    def show_frame():
        if webcam_running:
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img = img.resize((600, 400))
                imgtk = ImageTk.PhotoImage(image=img)
                webcam_label.imgtk = imgtk
                webcam_label.config(image=imgtk)
            webcam_label.after(10, show_frame)

    # Capture Image from Webcam
    def capture_image():
        if not daily_routine:
            messagebox.showwarning("Daily Routine Missing", "Please enter your daily routine before capturing an image.")
            return

        if webcam_running:
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img.save("captured_image.png")
                messagebox.showinfo("Image Captured", "Image has been captured and saved as captured_image.png")
                # Run stress analysis in a separate thread
                threading.Thread(target=analyze_stress, args=(frame,)).start()

    # Analyze Stress Based on Captured Image
    def analyze_stress(frame):
        try:
            # Detect faces in the frame
            faces, gray_frame = detect_faces(face_cascade, frame)

            if len(faces) == 0:
                messagebox.showwarning("No Face Detected", "No face detected in the captured image.")
                return

            # Crop the first detected face
            (x, y, w, h) = faces[0]
            face = gray_frame[y:y+h, x:x+w]

            # Preprocess the face for emotion analysis
            reshaped_face = preprocess_face(face)

            # Predict emotion
            emotion, confidence = predict_emotion(emotion_model, reshaped_face)

            # Calculate initial stress level based on emotion
            stress_level = calculate_stress_level(emotion)

            # Update the GUI with the analysis results
            root.after(0, update_gui, emotion, stress_level)
            save_analysis_result(emotion, stress_level)
        except Exception as e:
            logging.error(f"Error in stress analysis: {e}")

    # Update GUI with Analysis Results
    def update_gui(emotion, stress_level):
        # Clear previous results
        analysis_label.config(text=f"Emotion: {emotion}", fg="#ffffff")
        stress_level_label.config(text=f"Stress Level: {stress_level}", fg="#ffffff")
        recommendation_label.config(text=f"Recommendation: {get_recommendation(stress_level)}", fg="#ffffff")

    # Save Analysis Result to MongoDB
    def save_analysis_result(emotion, stress_level):
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            recommendation = get_recommendation(stress_level)
            entry = {
                "timestamp": timestamp,
                "emotion": emotion,
                "stress_level": stress_level,
                "user": current_user,
                "recommendation": recommendation,
                "daily_routine": daily_routine
            }
            collection.insert_one(entry)
            logging.info(f"Analysis result saved for user {current_user}.")
        except Exception as e:
            logging.error(f"Failed to save analysis: {str(e)}")
            messagebox.showerror("Database Error", f"Failed to save analysis: {str(e)}")

    # Clear History Function
    def clear_history():
        if not current_user:
            messagebox.showwarning("No User", "Please log in to clear history.")
            return

        # Confirm with the user
        confirm = messagebox.askyesno("Clear History", "Are you sure you want to clear your analysis history?")
        if confirm:
            try:
                # Delete all entries for the current user
                collection.delete_many({"user": current_user})
                logging.info(f"Analysis history cleared for user {current_user}.")
                messagebox.showinfo("Success", "Analysis history cleared successfully!")
            except Exception as e:
                logging.error(f"Failed to clear history: {str(e)}")
                messagebox.showerror("Error", f"Failed to clear history: {str(e)}")

    # Show History Function
    def show_history():
        if not current_user:
            messagebox.showwarning("No User", "Please log in to view history.")
            return

        try:
            # Fetch all analysis results for the current user
            history = list(collection.find({"user": current_user}, {"_id": 0, "timestamp": 1, "emotion": 1, "stress_level": 1, "recommendation": 1}))

            if not history:
                messagebox.showinfo("No Data", "No history found.")
                return

            # Create a new window to display the history
            history_window = tk.Toplevel(root)
            history_window.title(f"Analysis History - {current_user}")
            history_window.geometry("800x600")
            history_window.configure(bg="#2c3e50")

            # Create a text widget to display the history
            history_text = tk.Text(history_window, font=label_font, bg="#34495e", fg="#ffffff", wrap="word")
            history_text.pack(fill="both", expand=True, padx=10, pady=10)

            # Insert the history data into the text widget
            for entry in history:
                history_text.insert("end", f"Timestamp: {entry['timestamp']}\n")
                history_text.insert("end", f"Emotion: {entry['emotion']}\n")
                history_text.insert("end", f"Stress Level: {entry['stress_level']}\n")
                history_text.insert("end", f"Recommendation: {entry['recommendation']}\n")
                history_text.insert("end", "-" * 50 + "\n\n")

            # Disable the text widget to prevent editing
            history_text.config(state="disabled")

        except Exception as e:
            logging.error(f"Failed to fetch history: {str(e)}")
            messagebox.showerror("Error", f"Failed to fetch history: {str(e)}")

    # Stress Analysis Dashboard
    def show_stress_dashboard():
        if not current_user:
            messagebox.showwarning("No User", "Please log in to view the dashboard.")
            return

        # Fetch stress level history for the current user
        try:
            history = list(collection.find({"user": current_user}, {"_id": 0, "timestamp": 1, "stress_level": 1}))
            if not history:
                messagebox.showinfo("No Data", "No stress level history found.")
                return

            # Prepare data for plotting
            timestamps = [entry["timestamp"] for entry in history]
            stress_levels = [entry["stress_level"] for entry in history]

            # Create a new window for the dashboard
            dashboard_window = tk.Toplevel(root)
            dashboard_window.title(f"Stress Analysis Dashboard - {current_user}")
            dashboard_window.geometry("800x600")
            dashboard_window.configure(bg="#2c3e50")

            # Create a figure and plot the data
            fig, ax = plt.subplots(figsize=(8, 6))

            # Set a font that supports emojis
            plt.rcParams['font.family'] = 'Segoe UI Emoji'  # Use 'Noto Color Emoji' on non-Windows platforms

            ax.plot(timestamps, stress_levels, marker='o', linestyle='-', color='b')
            ax.set_title(f"Stress Level Over Time - {current_user}")
            ax.set_xlabel("Timestamp")
            ax.set_ylabel("Stress Level")
            ax.grid(True)
            plt.xticks(rotation=45)

            # Embed the plot in the Tkinter window
            canvas = FigureCanvasTkAgg(fig, master=dashboard_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        except Exception as e:
            logging.error(f"Failed to fetch stress level history: {str(e)}")
            messagebox.showerror("Error", f"Failed to fetch stress level history: {str(e)}")

    # Daily Routine Input Section
    def enter_daily_routine():
        global daily_routine
        routine_window = tk.Toplevel(root)
        routine_window.title("Enter Daily Routine")
        routine_window.geometry("500x300")
        routine_window.configure(bg="#2c3e50")

        routine_label = tk.Label(routine_window, text="Please enter your daily routine (e.g., work, exercise, sleep):", font=label_font, bg="#2c3e50", fg="#ffffff")
        routine_label.pack(pady=10)

        routine_entry = tk.Entry(routine_window, font=label_font, width=40, bg="#34495e", fg="#ffffff")
        routine_entry.pack(pady=10)

        def save_routine():
            global daily_routine
            daily_routine = routine_entry.get()
            routine_window.destroy()
            messagebox.showinfo("Routine Saved", "Your daily routine has been saved!")

        save_button = tk.Button(routine_window, text="Save Routine", font=button_font, bg="#4caf50", fg="white", command=save_routine)
        save_button.pack(pady=10)

    # Login Section
    def login():
        global current_user
        username = username_entry.get()
        password = password_entry.get()

        if authenticate_user(username, password):
            current_user = username
            messagebox.showinfo("Login Success", "Login Successful!")
            login_frame.pack_forget()
            app_frame.pack(fill="both", expand=True)
        else:
            messagebox.showerror("Login Error", "Invalid Username or Password")

    # Signup Section
    def signup():
        username = username_entry.get()
        password = password_entry.get()
        
        if register_user(username, password):
            messagebox.showinfo("Signup Success", "Account created successfully!")
        else:
            messagebox.showerror("Signup Error", "Username already exists.")

    # Create the login/signup screen
    login_frame = tk.Frame(root, bg="#2c3e50")
    login_frame.pack(fill="both", expand=True)

    # Add a colorful box for the login/signup section
    login_box = tk.Frame(login_frame, bg="#34495e", bd=2, relief="ridge")
    login_box.pack(pady=50, padx=50, fill="both", expand=True)

    login_or_signup_label = tk.Label(login_box, text="Login or Sign Up", font=title_font, bg="#34495e", fg="#4caf50")
    login_or_signup_label.pack(pady=20)

    username_label = tk.Label(login_box, text="Username", font=label_font, bg="#34495e", fg="#ffffff")
    username_label.pack(pady=5)

    username_entry = tk.Entry(login_box, font=label_font, bg="#34495e", fg="#ffffff")
    username_entry.pack(pady=5)

    password_label = tk.Label(login_box, text="Password", font=label_font, bg="#34495e", fg="#ffffff")
    password_label.pack(pady=5)

    password_entry = tk.Entry(login_box, font=label_font, show="*", bg="#34495e", fg="#ffffff")
    password_entry.pack(pady=5)

    login_button = tk.Button(login_box, text="Login", font=button_font, bg="#4caf50", fg="white", command=login)
    login_button.pack(pady=10)

    signup_button = tk.Button(login_box, text="Sign Up", font=button_font, bg="#ff6347", fg="white", command=signup)
    signup_button.pack(pady=10)

    # Create the main app frame (hidden initially)
    app_frame = tk.Frame(root, bg="#2c3e50")
    app_frame.pack_forget()

    # Add components for the main app screen
    title_label = tk.Label(app_frame, text="Stress Level Management System", font=title_font, bg="#2c3e50", fg="#4caf50")
    title_label.pack(pady=20)

    webcam_label = tk.Label(app_frame, bg="#2c3e50")
    webcam_label.pack(pady=20)

    button_frame = tk.Frame(app_frame, bg="#2c3e50")
    button_frame.pack(pady=10)

    start_button = tk.Button(button_frame, text="Start Webcam", font=button_font, bg="#4caf50", fg="white", command=start_webcam)
    start_button.pack(side="left", padx=10)

    stop_button = tk.Button(button_frame, text="Stop Webcam", font=button_font, bg="#ff6347", fg="white", command=stop_webcam)
    stop_button.pack(side="left", padx=10)

    capture_button = tk.Button(button_frame, text="Capture Image", font=button_font, bg="#4caf50", fg="white", command=capture_image)
    capture_button.pack(side="left", padx=10)

    enter_routine_button = tk.Button(button_frame, text="Enter Daily Routine", font=button_font, bg="#4caf50", fg="white", command=enter_daily_routine)
    enter_routine_button.pack(side="left", padx=10)

    clear_history_button = tk.Button(button_frame, text="Clear History", font=button_font, bg="#ff6347", fg="white", command=clear_history)
    clear_history_button.pack(side="left", padx=10)

    dashboard_button = tk.Button(button_frame, text="Stress Dashboard", font=button_font, bg="#4caf50", fg="white", command=show_stress_dashboard)
    dashboard_button.pack(side="left", padx=10)

    show_history_button = tk.Button(button_frame, text="Show History", font=button_font, bg="#4caf50", fg="white", command=show_history)
    show_history_button.pack(side="left", padx=10)

    # Add borders for emotion, stress level, and recommendation
    result_frame = tk.Frame(app_frame, bg="#2c3e50")
    result_frame.pack(pady=20)

    emotion_frame = tk.Frame(result_frame, bg="#34495e", bd=2, relief="ridge")
    emotion_frame.pack(pady=10, padx=10, fill="x")

    analysis_label = tk.Label(emotion_frame, text="Emotion: ", font=label_font, bg="#34495e", fg="#ffffff")
    analysis_label.pack(pady=10)

    stress_level_frame = tk.Frame(result_frame, bg="#34495e", bd=2, relief="ridge")
    stress_level_frame.pack(pady=10, padx=10, fill="x")

    stress_level_label = tk.Label(stress_level_frame, text="Stress Level: ", font=label_font, bg="#34495e", fg="#ffffff")
    stress_level_label.pack(pady=10)

    recommendation_frame = tk.Frame(result_frame, bg="#34495e", bd=2, relief="ridge")
    recommendation_frame.pack(pady=10, padx=10, fill="x")

    recommendation_label = tk.Label(recommendation_frame, text="Recommendation: ", font=label_font, bg="#34495e", fg="#ffffff")
    recommendation_label.pack(pady=10)

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    create_gui(root)
    root.mainloop()