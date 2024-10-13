import sys
import threading

import psutil
import time
import os
import pygame
from playsound import playsound

forbidden_processes = ['msedge.exe']
working_time = 25 * 60
pause_time = 5 * 60
big_pause_time = 900
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
    programm_was_killed = False
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] in forbidden_processes:
            try:
                os.kill(process.info['pid'], 9)
                programm_was_killed = True
            except Exception as e:
                print(f"Failed to kill process {process.info['name']} with PID {process.info['pid']}: {e}")
    return programm_was_killed


def end_working_phase():
    global working_sessions
    global current_mode
    global timer
    global session_per_cycle
    working_sessions += 1
    timer.reset()
    if working_sessions == session_per_cycle:
        working_sessions = 0
        current_mode = "big pause"
    else:
        current_mode = "pause"
    timer.start()


def end_pause_phase():
    global current_mode
    global timer
    timer.reset()
    current_mode = "working"
    timer.start()


def main():
    global current_mode
    global timer
    global alarm
    global working_sessions
    global session_per_cycle
    pygame.mixer.init()

    edge_kill_counter = 0
    timer = Timer()
    timer.start()

    while True:
        if current_mode == "working":
            target_time = working_time
        elif current_mode == "pause":
            target_time = pause_time
        else:
            target_time = big_pause_time
        print(
            f"\r{current_mode}: {int(timer.elapsed())}s/{target_time}s. Session {working_sessions + 1}/{session_per_cycle} Time is paused: {timer.is_paused}. edges killed: {edge_kill_counter}",
            end='')
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

        time.sleep(1)


def monitor_input():
    global timer
    global current_mode
    while True:
        input_text = sys.stdin.readline().strip()
        if input_text.lower() == 'p':
            timer.stop()
        elif input_text.lower() == 'n':
            if current_mode == "working":
                end_working_phase()
            else:
                end_pause_phase()
        elif input_text.lower() == 'r':
            timer.continue_timer()
        elif input_text.lower() == 'q':
            os._exit(0)

        time.sleep(0.5)


if __name__ == "__main__":
    input_thread = threading.Thread(target=monitor_input, daemon=True)
    input_thread.start()
    main()
