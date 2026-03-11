import random
import sqlite3

def generate_bayes_question_text():
    PA = round(random.uniform(0.3, 0.7), 2)

    PB_A = round(random.uniform(0.2, 0.6), 2)
    PB_notA = round(random.uniform(0.05, 0.3), 2)

    PC_B = round(random.uniform(0.2, 0.6), 2)
    PC_notB = round(random.uniform(0.01, 0.2), 2)

    text = f"""
Se consideră următoarea rețea bayesiană:

P(A = true) = {PA}

P(B = true | A = true) = {PB_A}
P(B = true | A = false) = {PB_notA}

P(C = true | B = true) = {PC_B}
P(C = true | B = false) = {PC_notB}

Structura rețelei este:
A → B → C

Cerință:
Calculați probabilitatea marginală P(C = true).
""".strip()

    return text


def populate_bayes_questions(db_path="database.db", n=50):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for _ in range(n):
        q = generate_bayes_question_text()
        cursor.execute(
            "INSERT INTO bayes_questions (question_text) VALUES (?)",
            (q,)
        )

    conn.commit()
    conn.close()