import re

def parse_user_assignment(text: str) -> dict:
    """
    Extrage perechi de forma:
    X1 = 2
    X12=3
    din orice text trimis de utilizator.
    """
    assignment = {}
    matches = re.findall(r"(X\d+)\s*=\s*(\d+)", text)
    for var, val in matches:
        assignment[var] = int(val)
    return assignment
