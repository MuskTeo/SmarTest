import re

def parse_bayes_question(text):
    def extract(pattern):
        return float(re.search(pattern, text).group(1))

    PA = extract(r"P\(A\s*=\s*true\)\s*=\s*([0-9.]+)")
    PB_A = extract(r"P\(B\s*=\s*true\s*\|\s*A\s*=\s*true\)\s*=\s*([0-9.]+)")
    PB_notA = extract(r"P\(B\s*=\s*true\s*\|\s*A\s*=\s*false\)\s*=\s*([0-9.]+)")
    PC_B = extract(r"P\(C\s*=\s*true\s*\|\s*B\s*=\s*true\)\s*=\s*([0-9.]+)")
    PC_notB = extract(r"P\(C\s*=\s*true\s*\|\s*B\s*=\s*false\)\s*=\s*([0-9.]+)")

    return PA, PB_A, PB_notA, PC_B, PC_notB


def solve_bayes_chain(PA, PB_A, PB_notA, PC_B, PC_notB):
    PB = PB_A * PA + PB_notA * (1 - PA)
    PC = PC_B * PB + PC_notB * (1 - PB)

    PB_r = round(PB, 4)
    PC_r = round(PC, 4)

    explanation = (
        "Pasul 1: Calculăm probabilitatea marginală P(B)\n"
        f"P(B) = P(B=true | A=true)·P(A=true) + P(B=true | A=false)·P(A=false)\n"
        f"P(B) = {PB_A}·{PA} + {PB_notA}·{round(1-PA,4)} = {PB_r}\n\n"
        "Pasul 2: Calculăm probabilitatea marginală P(C)\n"
        f"P(C) = P(C=true | B=true)·P(B) + P(C=true | B=false)·P(¬B)\n"
        f"P(C) = {PC_B}·{PB_r} + {PC_notB}·{round(1-PB,4)} = {PC_r}\n\n"
        "Rezultat final:\n"
        f"P(C = true) = {PC_r}"
    )

    return explanation


def parse_user_numeric_answer(text: str):
    if text is None:
        return None

    # prinde primul număr (int sau zecimal cu . sau ,)
    m = re.search(r"[-+]?\d+(?:[.,]\d+)?", str(text))
    if not m:
        return None

    return float(m.group(0).replace(",", "."))


def score_bayes_answer(user_value, correct_value, tol=0.02):
    if user_value is None or correct_value is None:
        return 0.0
    correct = extract_last_number(correct_value)
    if correct is None:
        return 0.0

    diff = abs(user_value - correct)


    if diff <= tol:
        return 1.0
    if diff <= 2 * tol:
        return 0.6
    if diff <= 3 * tol:
        return 0.3
    return 0.0


# OPTIONAL: dacă vrei să folosești extract_number pentru stringuri gen "P(C)=0,2069"
def extract_number(s):
    if s is None:
        return None
    m = re.search(r"[-+]?\d+(?:[.,]\d+)?", str(s))
    return float(m.group(0).replace(",", ".")) if m else None


def extract_last_number(text: str):
    nums = re.findall(r"[-+]?\d+(?:[.,]\d+)?", str(text))
    if not nums:
        return None
    return float(nums[-1].replace(",", "."))