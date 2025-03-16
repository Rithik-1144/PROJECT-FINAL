import tkinter as tk
import logging
from gui import create_gui

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    try:
        # Create the main application window
        root = tk.Tk()
        root.title("Stress Level Management System")
        root.geometry("1000x700")
        root.configure(bg="#f0f8ff")

        # Create the GUI
        create_gui(root)

        # Start the main loop
        root.mainloop()
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()