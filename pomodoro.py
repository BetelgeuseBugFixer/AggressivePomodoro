import sys
import psutil
import time
import os
import pygame
import tkinter as tk

forbidden_processes = ['msedge.exe']
working_time = 25 * 60
pause_time = 5 * 60
big_pause_time = 15 * 60
working_sessions = 0
mercy_time = 30
current_mode = "working"
alarm = "clock-alarm-8761.mp3"
timer = None
session_per_cycle = 4


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


def kill_edge():
    program_was_killed = False
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] in forbidden_processes:
            try:
                os.kill(process.info['pid'], 9)
                program_was_killed = True
            except Exception as e:
                print(f"Failed to kill process {process.info['name']} with PID {process.info['pid']}: {e}")
    return program_was_killed


def end_working_phase():
    global working_sessions
    global current_mode
    global timer
    global session_per_cycle
    working_sessions += 1
    timer.reset()
    if working_sessions == session_per_cycle:
        current_mode = "big pause"
    else:
        current_mode = "pause"
    timer.start()


def end_pause_phase():
    global current_mode
    global timer
    global session_per_cycle
    global working_sessions
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

    time_label.config(text=f"{current_mode}: {int(timer.elapsed())}s/{target_time}s")
    session_label.config(text=f"Sessions Done: {working_sessions}/{session_per_cycle}")
    edge_label.config(text=f"Edges Killed: {edge_kill_counter}")
    paused_label.config(text=f"Time is Paused: {timer.is_paused}")

    if current_mode == "working":
        if timer.elapsed() > working_time:
            end_working_phase()
            pygame.mixer.music.load(alarm)
            pygame.mixer.music.play()
        elif timer.elapsed() > mercy_time:
            if kill_edge():
                edge_kill_counter += 1

    elif current_mode == "pause":
        if timer.elapsed() > pause_time:
            end_pause_phase()
            pygame.mixer.music.load(alarm)
            pygame.mixer.music.play()

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
        end_working_phase()
    else:
        end_pause_phase()


def resume_timer():
    timer.continue_timer()


def quit_program():
    root.destroy()
    sys.exit(0)


if __name__ == "__main__":
    pygame.mixer.init()

    edge_kill_counter = 0
    timer = Timer()
    timer.start()

    root = tk.Tk()
    root.title("Pomodoro Timer")

    time_label = tk.Label(root, text="", font=("Helvetica", 18))
    time_label.pack()

    session_label = tk.Label(root, text="", font=("Helvetica", 14))
    session_label.pack()

    edge_label = tk.Label(root, text="", font=("Helvetica", 14))
    edge_label.pack()

    paused_label = tk.Label(root, text="", font=("Helvetica", 14))
    paused_label.pack()

    pause_button = tk.Button(root, text="Pause", command=pause_timer)
    pause_button.pack(side=tk.LEFT)

    next_button = tk.Button(root, text="Next Phase", command=next_phase)
    next_button.pack(side=tk.LEFT)

    resume_button = tk.Button(root, text="Resume", command=resume_timer)
    resume_button.pack(side=tk.LEFT)

    quit_button = tk.Button(root, text="Quit", command=quit_program)
    quit_button.pack(side=tk.LEFT)

    root.after(1000, update_ui)
    root.mainloop()
