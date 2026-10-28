"""Local actions that the offline assistant is allowed to perform."""

from __future__ import annotations

import ctypes
import datetime as dt
import json
import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Callable

from core import Ears, Mouth, PROJECT_DIR


class AssistantSkills:
    def __init__(self, mouth: Mouth | None = None, ears: Ears | None = None) -> None:
        self.mouth = mouth or Mouth()
        self.ears = ears or Ears()
        self.profile_path = PROJECT_DIR / "data" / "profile.json"
        self.profile = self.load_profile()
        self.actions: dict[str, Callable[[], None]] = {
            "change_ai_name": self.change_ai_name,
            "set_user_name": self.set_user_name,
            "set_user_dob": self.set_user_dob,
            "who_am_i": self.who_am_i,
            "who_is_user": self.who_is_user,
            "greeting": self.greeting,
            "date_time": self.date_time,
            "browser": self.browser,
            "notepad": self.notepad,
            "volume_up": self.volume_up,
            "volume_down": self.volume_down,
            "lock_system": self.lock_system,
            "shutdown": self.shutdown,
        }

    def load_profile(self) -> dict[str, str]:
        default = {"ai_name": "Mini Assistant", "user_name": "Vignesh", "user_dob": "Unknown"}
        try:
            with self.profile_path.open("r", encoding="utf-8") as file:
                saved = json.load(file)
            if isinstance(saved, dict):
                default.update({key: str(value) for key, value in saved.items() if key in default})
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return default

    def save_profile(self) -> None:
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        with self.profile_path.open("w", encoding="utf-8") as file:
            json.dump(self.profile, file, indent=2)

    def execute(self, intent_name: str) -> bool:
        action = self.actions.get(intent_name)
        if action is None:
            return False
        action()
        return True

    def change_ai_name(self) -> None:
        self.mouth.speak("What would you like to call me?")
        name = self.ears.listen()
        if name and name != "exit":
            self.profile["ai_name"] = name.title()
            self.save_profile()
            self.mouth.speak(f"Name saved. I am now {self.profile['ai_name']}.")

    def set_user_name(self) -> None:
        self.mouth.speak("What is your name?")
        name = self.ears.listen()
        if name and name != "exit":
            self.profile["user_name"] = name.title()
            self.save_profile()
            self.mouth.speak(f"Nice to meet you, {self.profile['user_name']}.")

    def set_user_dob(self) -> None:
        self.mouth.speak("When is your birthday? For example, January first.")
        birthday = self.ears.listen()
        if birthday and birthday != "exit":
            self.profile["user_dob"] = birthday
            self.save_profile()
            self.mouth.speak("Birthday saved.")

    def who_am_i(self) -> None:
        self.mouth.speak(f"I am {self.profile['ai_name']}, your local assistant.")

    def who_is_user(self) -> None:
        self.mouth.speak(f"You are {self.profile['user_name']}. Your birthday is {self.profile['user_dob']}.")

    def greeting(self) -> None:
        self.mouth.speak(f"Hello {self.profile['user_name']}. {self.profile['ai_name']} is online.")

    def date_time(self) -> None:
        self.mouth.speak(f"It is {dt.datetime.now().strftime('%I:%M %p')}.")

    def browser(self) -> None:
        self.mouth.speak("Opening your default browser.")
        webbrowser.open("https://www.google.com")

    def notepad(self) -> None:
        self.mouth.speak("Opening Notepad.")
        subprocess.Popen(["notepad.exe"])

    def _change_volume(self, key: str, message: str) -> None:
        try:
            import pyautogui

            pyautogui.press(key, presses=5)
            self.mouth.speak(message)
        except ImportError:
            self.mouth.speak("Volume control needs the optional pyautogui package.")

    def volume_up(self) -> None:
        self._change_volume("volumeup", "Volume increased.")

    def volume_down(self) -> None:
        self._change_volume("volumedown", "Volume decreased.")

    def lock_system(self) -> None:
        self.mouth.speak("Say confirm to lock the computer.")
        if self.ears.listen() == "confirm":
            ctypes.windll.user32.LockWorkStation()

    def shutdown(self) -> None:
        self.mouth.speak("Say confirm to shut down the computer in five seconds.")
        if self.ears.listen() == "confirm":
            os.system("shutdown /s /t 5")
