from __future__ import annotations


ROBOT_FOLDER_COMMAND = "robot folder"
MY_IMPORTANT_INFO_COMMAND = "mi información importante"
WHAT_ROBBIE_KNOWS_COMMAND = "lo que robbie sabe"
WHAT_DOES_ROBBIE_KNOW_COMMAND = "what does robbie know"


def is_robot_folder_command(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {
        ROBOT_FOLDER_COMMAND,
        MY_IMPORTANT_INFO_COMMAND,
        WHAT_ROBBIE_KNOWS_COMMAND,
        WHAT_DOES_ROBBIE_KNOW_COMMAND,
    }
