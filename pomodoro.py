import sys
import platform
from tkinter import ttk
import tkinter as tk
import psutil
import time
import os
import pygame
import json

# define global variables
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

if platform.system() == "Darwin":
    forbidden_processes = ["Microsoft Edge"]
else:
    forbidden_processes = ["msedge.exe"]

working_time = 25 * 60
pause_time = 5 * 60
big_pause_time = 15 * 60
working_sessions = 0
mercy_time = 30
current_mode = "working"
alarm = "clock-alarm-8761.mp3"
timer = None
session_per_cycle = 4

# Theme colors per mode, used both for the window bg and for the ttk button style
THEMES = {
    "working": "lightcoral",
    "pause": "lightgreen",
    "big pause": "lightblue",
}


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


class Timer:
    def __init__(self):
        self.last_time_start = None
        self.elapsed_time = 0
        self.is_paused = True

    def start(self):
        self.last_time_start = time.perf_counter()
        self.elapsed_time = 0
        self.is_paused = False

    def stop(self):
        if not self.is_paused:
            new_time = time.perf_counter()
            self.elapsed_time += new_time - self.last_time_start
            self.last_time_start = new_time
            self.is_paused = True

    def continue_timer(self):
        if self.is_paused:
            self.last_time_start = time.perf_counter()
            self.is_paused = False
        else:
            print("Timer is not paused and cannot be continued")

    def elapsed(self):
        if not self.is_paused:
            new_time = time.perf_counter()
            self.elapsed_time += new_time - self.last_time_start
            self.last_time_start = new_time
        return self.elapsed_time

    def reset(self):
        self.last_time_start = None
        self.elapsed_time = 0
        self.is_paused = True


def format_seconds(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{int(minutes)}:{int(seconds):02}"


def kill_edge():
    program_was_killed = False
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] in forbidden_processes:
            try:
                process.kill()
                program_was_killed = True
            except psutil.NoSuchProcess:
                pass
            except psutil.AccessDenied:
                print(f"Access denied to kill {process.info['name']} (PID: {process.info['pid']}).")
            except Exception as e:
                print(f"Failed to kill {process.info['name']}: {e}")
    return program_was_killed


def set_theme(mode):
    bg_color = THEMES.get(mode, "lightcoral")
    fg_color = "black"

    root.configure(bg=bg_color)

    labels = [
        time_label, session_label, edge_label, paused_label,
        working_label, pause_label, big_pause_label, sessions_label,
    ]
    for widget in labels:
        widget.configure(bg=bg_color, fg=fg_color)

    # set style
    style.configure("Themed.TButton", background=bg_color, foreground=fg_color)
    style.map("Themed.TButton", background=[("active", bg_color)])


def pop_up_window(text):
    root.deiconify()  # make root visible again if it was minimized
    root.lift()
    # create pop up
    popup = tk.Toplevel()
    popup.title("New Phase")
    popup.geometry("300x100")
    popup.resizable(False, False)

    # play alarm
    pygame.mixer.music.load(alarm)
    pygame.mixer.music.play(loops=-1)

    label = tk.Label(popup, text=text, font=("Helvetica", 14))
    label.pack(padx=20, pady=10)

    ok_button = tk.Button(popup, text="OK", font=("Helvetica", 12), command=popup.destroy)
    ok_button.pack(pady=5)

    popup.transient(root)
    popup.grab_set()
    popup.focus_force()
    popup.attributes("-topmost", True)

    def stop_alarm_on_close():
        pygame.mixer.music.stop()
        popup.destroy()

    ok_button.configure(command=stop_alarm_on_close)
    popup.bind("<Escape>", lambda event: stop_alarm_on_close())
    popup.wait_window()


def end_working_phase(create_pop_up=True):
    global working_sessions
    global current_mode
    global timer
    global session_per_cycle
    if create_pop_up:
        pop_up_window("Break Time")
    working_sessions += 1
    timer.reset()
    if working_sessions == session_per_cycle:
        current_mode = "big pause"
    else:
        current_mode = "pause"
    timer.start()


def end_pause_phase(create_pop_up=True):
    global current_mode
    global timer
    global session_per_cycle
    global working_sessions
    if create_pop_up:
        pop_up_window("Back To Work")
    if working_sessions == session_per_cycle:
        working_sessions = 0
    timer.reset()
    current_mode = "working"
    timer.start()


def update_ui():
    global current_mode
    global timer
    global alarm
    global working_sessions
    global session_per_cycle
    global edge_kill_counter

    if current_mode == "working":
        target_time = working_time
    elif current_mode == "pause":
        target_time = pause_time
    else:
        target_time = big_pause_time

    set_theme(current_mode)

    elapsed = int(timer.elapsed())

    # update bar
    percent = min(elapsed / target_time * 100, 100)
    progressbar["value"] = percent

    time_label.config(text=f"{current_mode}: {format_seconds(elapsed)} / {format_seconds(target_time)}")
    session_label.config(text=f"Sessions Done: {working_sessions}/{session_per_cycle}")
    edge_label.config(text=f"Edges Killed: {edge_kill_counter}")
    paused_label.config(text=f"Time is Paused: {timer.is_paused}")

    if current_mode == "working":
        if timer.elapsed() > working_time:
            end_working_phase()
        elif timer.elapsed() > mercy_time:
            if kill_edge():
                edge_kill_counter += 1

    elif current_mode == "pause":
        if timer.elapsed() > pause_time:
            end_pause_phase()

    elif current_mode == "big pause":
        if timer.elapsed() > big_pause_time:
            end_pause_phase()
            pygame.mixer.music.load(alarm)
            pygame.mixer.music.play()

    root.after(1000, update_ui)


def pause_timer():
    timer.stop()


def next_phase():
    if current_mode == "working":
        end_working_phase(create_pop_up=False)
    else:
        end_pause_phase(create_pop_up=False)


def resume_timer():
    timer.continue_timer()


def quit_program():
    root.destroy()
    sys.exit(0)


def update_configs():
    global working_time, pause_time, big_pause_time, session_per_cycle, config

    try:
        # load new times and convert to seconds
        working_time = int(working_entry.get()) * 60
        pause_time = int(pause_entry.get()) * 60
        big_pause_time = int(big_pause_entry.get()) * 60
        session_per_cycle = int(sessions_entry.get())

        config["working_time"] = working_time
        config["pause_time"] = pause_time
        config["big_pause_time"] = big_pause_time
        config["session_per_cycle"] = session_per_cycle

        save_config(config)

    except ValueError:
        print("Invalid time value(s)")


if __name__ == "__main__":
    pygame.mixer.init()

    # load configs
    if os.path.isfile(CONFIG_FILE):
        config = load_config()
        # convert from minutes to seconds
        working_time = config["working_time"]
        pause_time = config["pause_time"]
        big_pause_time = config["big_pause_time"]
        mercy_time = config["mercy_time"]
        session_per_cycle = config["session_per_cycle"]
        forbidden_processes = config["forbidden_processes"]
    else:
        config = {"working_time": working_time, "pause_time": pause_time, "big_pause_time": big_pause_time,
                  "mercy_time": mercy_time, "session_per_cycle": session_per_cycle,
                  "forbidden_processes": forbidden_processes, }
        save_config(config)

    edge_kill_counter = 0
    timer = Timer()
    timer.start()

    root = tk.Tk()
    root.title("Pomodoro Timer")

    style = ttk.Style()
    style.theme_use("clam")

    time_label = tk.Label(root, text="", font=("Helvetica", 18))
    time_label.pack()

    session_label = tk.Label(root, text="", font=("Helvetica", 14))
    session_label.pack()

    edge_label = tk.Label(root, text="", font=("Helvetica", 14))
    edge_label.pack()

    paused_label = tk.Label(root, text="", font=("Helvetica", 14))
    paused_label.pack()

    progress = tk.DoubleVar()
    progressbar = ttk.Progressbar()
    progressbar.pack()

    working_label = tk.Label(root, text="Working Time (Minutes):")
    working_label.pack()
    working_entry = tk.Entry(root)
    working_entry.insert(0, str(working_time // 60))
    working_entry.pack()

    pause_label = tk.Label(root, text="Pause Time (Minutes):")
    pause_label.pack()
    pause_entry = tk.Entry(root)
    pause_entry.insert(0, str(pause_time // 60))
    pause_entry.pack()

    big_pause_label = tk.Label(root, text="Big Pause Time (Minutes):")
    big_pause_label.pack()
    big_pause_entry = tk.Entry(root)
    big_pause_entry.insert(0, str(big_pause_time // 60))
    big_pause_entry.pack()

    sessions_label = tk.Label(root, text="Sessions per Cycle:")
    sessions_label.pack()
    sessions_entry = tk.Entry(root)
    sessions_entry.insert(0, str(session_per_cycle))
    sessions_entry.pack()

    save_button = ttk.Button(root, text="Update Configs", command=update_configs, style="Themed.TButton")
    save_button.pack()

    pause_button = ttk.Button(root, text="Pause", command=pause_timer, style="Themed.TButton")
    pause_button.pack(side=tk.LEFT)

    next_button = ttk.Button(root, text="Next Phase", command=next_phase, style="Themed.TButton")
    next_button.pack(side=tk.LEFT)

    resume_button = ttk.Button(root, text="Resume", command=resume_timer, style="Themed.TButton")
    resume_button.pack(side=tk.LEFT)

    quit_button = ttk.Button(root, text="Quit", command=quit_program, style="Themed.TButton")
    quit_button.pack(side=tk.LEFT)

    root.after(1000, update_ui)
    root.mainloop()