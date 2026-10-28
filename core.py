"""Offline building blocks for Mini Assistant.

The assistant deliberately has no cloud or LLM dependency. It recognizes a
small, editable set of commands from ``data/intents.json`` and can fall back to
typed input when a microphone is unavailable.
"""

from __future__ import annotations

import json
import importlib.util
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent


def _normalise(text: str) -> str:
    """Make command comparisons insensitive to punctuation and casing."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", text.lower())).strip()


class Mouth:
    """Print responses and, when available, say them through the default speaker."""

    def __init__(self, use_voice: bool = True) -> None:
        self.engine: Any | None = None
        if use_voice:
            try:
                import pyttsx3

                self.engine = pyttsx3.init()
            except Exception:
                self.engine = None

    def speak(self, message: str) -> None:
        print(f"Mini Assistant: {message}")
        if self.engine is not None:
            try:
                self.engine.say(message)
                self.engine.runAndWait()
            except Exception:
                # Audio failure must not stop typed-command mode.
                self.engine = None


class Ears:
    """Accept microphone speech when possible, otherwise accept typed commands."""

    def __init__(self, use_microphone: bool = True) -> None:
        self.recognizer: Any | None = None
        self.microphone: Any | None = None
        # Non-interactive runs (including automated tests) should not wait for a
        # microphone before consuming their supplied text input.
        if use_microphone and sys.stdin.isatty() and importlib.util.find_spec("pocketsphinx"):
            try:
                import speech_recognition as sr

                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
            except Exception:
                self.recognizer = None
                self.microphone = None

    def listen(self, prompt: str = "You: ") -> str:
        """Return a normalised command, or an empty string if none was supplied."""
        if self.recognizer is not None and self.microphone is not None:
            try:
                print("Listening... (type a command if microphone recognition fails)")
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                # PocketSphinx is local: it does not upload audio or need an API key.
                text = self.recognizer.recognize_sphinx(audio)
                print(f"You: {text}")
                return _normalise(text)
            except Exception:
                # Network, microphone, and recognition failures are expected on
                # some machines. The text fallback keeps every command usable.
                pass

        try:
            return _normalise(input(prompt))
        except (EOFError, KeyboardInterrupt):
            return "exit"


class SmartBrain:
    """A lightweight, deterministic intent matcher backed by JSON patterns."""

    def __init__(self, intents_path: str | Path | None = None) -> None:
        self.file_path = Path(intents_path) if intents_path else PROJECT_DIR / "data" / "intents.json"
        self.data: list[dict[str, Any]] = []
        self.patterns: list[tuple[str, str]] = []
        self.load_memory()

    def load_memory(self) -> None:
        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                raw_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            print(f"Could not load intents from {self.file_path}: {error}")
            return

        # Also accepts the old {"intents": [...]} format.
        source = raw_data.get("intents", []) if isinstance(raw_data, dict) else raw_data
        if not isinstance(source, list):
            print("Intent file must contain a list of intents.")
            return

        self.data = source
        for item in self.data:
            intent = item.get("intent") or item.get("tag")
            phrases = item.get("patterns") or item.get("user") or []
            if not isinstance(intent, str) or not isinstance(phrases, list):
                continue
            for phrase in phrases:
                if isinstance(phrase, str) and _normalise(phrase):
                    self.patterns.append((_normalise(phrase), intent))
        print(f"Loaded {len(self.patterns)} offline command patterns.")

    def classify(self, text: str) -> tuple[str, float]:
        command = _normalise(text)
        if not command or not self.patterns:
            return "unknown", 0.0

        best_intent = "unknown"
        best_score = 0.0
        command_words = set(command.split())
        for pattern, intent in self.patterns:
            if command == pattern:
                return intent, 1.0
            pattern_words = set(pattern.split())
            overlap = len(command_words & pattern_words) / len(command_words | pattern_words)
            sequence = SequenceMatcher(None, command, pattern).ratio()
            score = max(overlap, sequence * 0.85)
            if score > best_score:
                best_intent, best_score = intent, score

        # This avoids opening or locking things on a loosely related phrase.
        return (best_intent, best_score) if best_score >= 0.58 else ("unknown", best_score)

    def get_text_response(self, intent_name: str) -> str | None:
        for item in self.data:
            if item.get("intent", item.get("tag")) == intent_name:
                responses = item.get("responses") or item.get("bot") or []
                if responses:
                    return str(responses[0])
        return None
