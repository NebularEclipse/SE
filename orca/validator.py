import re


gmail_pattern = r"^[a-zA-Z0-9._%+-]+@gmail\.com$"
cspc_pattern = r"^[a-z]+@my\.cspc\.edu\.ph$"


def is_valid_email(email: str) -> bool:
    return (
        re.match(gmail_pattern, email) is not None
        or re.match(cspc_pattern, email) is not None
    )


def is_strong_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):  # Uppercase
        return False
    if not re.search(r"[a-z]", password):  # Lowercase
        return False
    if not re.search(r"\d", password):  # Digit
        return False
    if not re.search(r"[!@#$%^&*()_+=\-{}[\]:;\"'<>,.?/]", password):  # Special char
        return False
    return True
