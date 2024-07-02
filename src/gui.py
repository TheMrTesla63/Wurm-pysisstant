import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.ttk import Progressbar
from PIL import Image, ImageTk
import os
import re
import json
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Global variables to store the selected directories and player name
wurm_dir = ""
player_name = ""
log_file_path = ""
observer = None  # Initialize observer variable

# Global variables to store server uptime and meditation cooldown
server_uptime = None
last_meditation_time = None
meditation_count = 0

# Define regex patterns to match the log entries
LOGIN_PATTERN = re.compile(r"\[(\d{2}:\d{2}:\d{2})\] Welcome back, (.+)! Wurm has been waiting for you.")
UPTIME_PATTERN = re.compile(r"The server has been up (\d+) days, (\d+) hours and (\d+) minutes.")
MEDITATION_PATTERN = re.compile(r"\[(\d{2}:\d{2}:\d{2})\] You finish your meditation.")
COOLDOWN_PATTERN = re.compile(r"You can gain skill from meditating again in (\d+) minutes.* (\d+) more times today until you need to take a break.")

class LogFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == log_file_path:
            parse_log_file()

def parse_log_file():
    global server_uptime, last_meditation_time, meditation_count

    if not log_file_path:
        print("Log file path is not set.")
        return

    if not os.path.exists(log_file_path):
        print(f"Log file does not exist: {log_file_path}")
        return

    with open(log_file_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        print(f"Reading line: {line.strip()}")  # Debugging print

        uptime_match = UPTIME_PATTERN.search(line)
        if uptime_match:
            days, hours, minutes = map(int, uptime_match.groups())
            server_uptime = timedelta(days=days, hours=hours, minutes=minutes)
            print(f"Server Uptime matched: {server_uptime}")

        meditation_match = MEDITATION_PATTERN.search(line)
        if meditation_match:
            last_meditation_time = datetime.strptime(meditation_match.group(1), "%H:%M:%S").replace(
                year=datetime.now().year, 
                month=datetime.now().month, 
                day=datetime.now().day
            )
            print(f"Meditation matched: {last_meditation_time}")

        cooldown_match = COOLDOWN_PATTERN.search(line)
        if cooldown_match:
            meditation_count = 5 - int(cooldown_match.group(2))
            print(f"Meditation cooldown matched: {meditation_count}")

    update_progress_bar()

def update_progress_bar():
    if last_meditation_time and server_uptime:
        now = datetime.now()
        if meditation_count < 4:
            cooldown = timedelta(minutes=30)
        else:
            cooldown = timedelta(hours=3)
        
        elapsed = now - last_meditation_time
        remaining = cooldown - elapsed
        progress = min(elapsed / cooldown, 1.0) * 100
        progress_bar['value'] = progress

        print(f"Updating progress bar: {progress}%")  # Debugging print

        # Update the textual countdown
        if countdown_label.winfo_exists():
            if remaining > timedelta(0):
                countdown_label.config(text=f"Cooldown remaining: {str(remaining).split('.')[0]}")
                print(f"Cooldown remaining: {str(remaining).split('.')[0]}")  # Debugging print
            else:
                countdown_label.config(text="Meditation available now!")
                print("Meditation available now!")  # Debugging print
        else:
            return
    else:
        if countdown_label.winfo_exists():
            countdown_label.config(text="No recent meditation detected.")
            print("No recent meditation detected.")  # Debugging print
        else:
            return

    root.after(1000, update_progress_bar)

def open_timer_window():
    global progress_bar, countdown_label

    # Create a new window
    timer_window = tk.Toplevel()
    timer_window.title("Meditation Timer")
    
    # Set the size of the new window
    timer_window.geometry("300x150")
    
    # Add a progress bar
    progress_bar = Progressbar(timer_window, length=200, mode='determinate')
    progress_bar.pack(pady=20)
    
    # Add a label for the textual countdown
    countdown_label = tk.Label(timer_window, text="", font=("Helvetica", 12))
    countdown_label.pack(pady=10)

    update_progress_bar()

def select_directory():
    global wurm_dir
    wurm_dir = filedialog.askdirectory(title="Select Wurm Online Install Directory")
    if wurm_dir:
        selected_dir_label.config(text=f"Selected directory: {wurm_dir}")
        populate_players()
        save_settings()  # Save settings when directory is selected

def populate_players():
    global wurm_dir
    players_dir = os.path.join(wurm_dir, "players")
    if os.path.exists(players_dir):
        players = [name for name in os.listdir(players_dir) if os.path.isdir(os.path.join(players_dir, name))]
        player_dropdown['values'] = players
        if players:
            player_dropdown.current(0)
            select_player(None)

def select_player(event):
    global player_name, log_file_path
    player_name = player_dropdown.get()
    log_file_path = os.path.join(wurm_dir, "players", player_name, "logs", "_Event.2024-07.txt")
    selected_char_label.config(text=f"Selected character: {player_name}")
    start_log_monitor()
    save_settings()  # Save settings when player is selected

def start_log_monitor():
    global observer
    event_handler = LogFileHandler()
    
    # Stop previous observer if it exists
    if observer:
        observer.stop()
        observer.join()
    
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(log_file_path), recursive=False)
    observer.start()

def locate_logs_folder():
    global wurm_dir, player_name
    if wurm_dir and player_name:
        logs_path = os.path.join(wurm_dir, "players", player_name, "logs")
        if os.path.exists(logs_path):
            messagebox.showinfo("Logs Folder", f"Logs folder located: {logs_path}")
        else:
            messagebox.showerror("Error", "Logs folder not found")
    else:
        messagebox.showerror("Error", "Please select the Wurm Online directory and character")

def save_settings():
    settings = {
        "wurm_dir": wurm_dir,
        "player_name": player_name
    }
    with open("settings.txt", "w") as file:
        json.dump(settings, file)

def load_settings():
    global wurm_dir, player_name, log_file_path
    if os.path.exists("settings.txt"):
        with open("settings.txt", "r") as file:
            settings = json.load(file)
            wurm_dir = settings.get("wurm_dir", "")
            player_name = settings.get("player_name", "")
            log_file_path = os.path.join(wurm_dir, "players", player_name, "logs", "_Event.2024-07.txt")
            if wurm_dir:
                selected_dir_label.config(text=f"Selected directory: {wurm_dir}")
            if player_name:
                selected_char_label.config(text=f"Selected character: {player_name}")
                start_log_monitor()

def main():
    global root, selected_dir_label, selected_char_label, player_dropdown

    # Create the main window
    root = tk.Tk()
    root.title("Wurm Pysisstant")

    # Set the minimum size of the window
    root.minsize(300, 300)

    # Allow the window to be resizable
    root.resizable(True, True)

    # Create a frame for the images
    image_frame = tk.Frame(root)
    image_frame.pack(pady=10)

    # Path to the clock image
    clock_image_path = os.path.join(os.path.dirname(__file__), "../images/clock.png")

    # Path to the magnifying glass image
    magnifying_glass_image_path = os.path.join(os.path.dirname(__file__), "../images/magnifying_glass.png")

    # Path to the character image
    character_image_path = os.path.join(os.path.dirname(__file__), "../images/player.png")

    # Check if the clock image file exists
    if os.path.exists(clock_image_path):
        # Load and resize the clock image
        clock_image = Image.open(clock_image_path)
        clock_image = clock_image.resize((50, 50), Image.LANCZOS)
        clock_photo = ImageTk.PhotoImage(clock_image)
        # Create a button with the clock image
        timer_button = tk.Button(image_frame, image=clock_photo, compound=tk.LEFT, command=open_timer_window)
        timer_button.image = clock_photo  # Keep a reference to avoid garbage collection
        timer_button.grid(row=0, column=0, padx=10)
    else:
        # Create a button with the placeholder text "timer"
        timer_button = tk.Button(image_frame, text="timer", command=open_timer_window)
        timer_button.grid(row=0, column=0, padx=10)

    # Check if the magnifying glass image file exists
    if os.path.exists(magnifying_glass_image_path):
        # Load and resize the magnifying glass image
        magnifying_glass_image = Image.open(magnifying_glass_image_path)
        magnifying_glass_image = magnifying_glass_image.resize((50, 50), Image.LANCZOS)
        magnifying_glass_photo = ImageTk.PhotoImage(magnifying_glass_image)
        # Create a button with the magnifying glass image
        directory_button = tk.Button(image_frame, image=magnifying_glass_photo, compound=tk.LEFT, command=select_directory)
        directory_button.image = magnifying_glass_photo  # Keep a reference to avoid garbage collection
        directory_button.grid(row=0, column=1, padx=10)
    else:
        # Create a button with the placeholder text "Find Directory"
        directory_button = tk.Button(image_frame, text="Find Directory", command=select_directory)
        directory_button.grid(row=0, column=1, padx=10)

    # Check if the character image file exists
    if os.path.exists(character_image_path):
        # Load and resize the character image
        character_image = Image.open(character_image_path)
        character_image = character_image.resize((50, 50), Image.LANCZOS)
        character_photo = ImageTk.PhotoImage(character_image)
        # Create a button with the character image
        character_button = tk.Button(image_frame, image=character_photo, compound=tk.LEFT)
        character_button.image = character_photo  # Keep a reference to avoid garbage collection
        character_button.grid(row=0, column=2, padx=10)
    else:
        messagebox.showerror("Error", "Character image not found")

    # Create a dropdown for selecting the player
    player_dropdown = ttk.Combobox(root, state="readonly")
    player_dropdown.bind("<<ComboboxSelected>>", select_player)
    player_dropdown.pack(pady=20)

    # Button to locate logs folder
    logs_button = tk.Button(root, text="Locate Logs Folder", command=locate_logs_folder)
    logs_button.pack(pady=10)

    # Label to show the selected directory
    selected_dir_label = tk.Label(root, text="No directory selected", font=("Helvetica", 10))
    selected_dir_label.pack(pady=5)

    # Label to show the selected character
    selected_char_label = tk.Label(root, text="No character selected", font=("Helvetica", 10))
    selected_char_label.pack(pady=5)

    # Load settings when the application starts
    load_settings()

    # Run the main event loop
    root.mainloop()

if __name__ == "__main__":
    main()
