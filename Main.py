"""Start the local, rule-based Mini Assistant."""

from core import Ears, Mouth, SmartBrain
from Skills import AssistantSkills


def main() -> None:
    mouth = Mouth()
    ears = Ears()
    brain = SmartBrain()
    skills = AssistantSkills(mouth, ears)

    mouth.speak(f"Hello {skills.profile['user_name']}! {skills.profile['ai_name']} is online.")
    mouth.speak("Say or type a command. Say help to hear examples, or exit to close.")

    while True:
        text = ears.listen()
        if not text:
            continue
        if text in {"exit", "quit", "goodbye", "stop"}:
            mouth.speak("Goodbye!")
            break

        intent, confidence = brain.classify(text)
        print(f"[Debug] Intent: {intent} ({confidence:.2f})")

        if intent == "unknown":
            mouth.speak("I do not know that command yet. Say help for examples.")
        elif not skills.execute(intent):
            response = brain.get_text_response(intent)
            mouth.speak(response or "I understood that, but there is no action for it yet.")


if __name__ == "__main__":
    main()
