import sqlite3
import random
import json
import os
from RandomGameGenerator import generate_random_game, hardcoded_games
from Variabile import generate_csp_question_text, generate_random_csp
from Graphgenerator import *
from Bayesgenerator import *
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INFOS_PATH = os.path.join(BASE_DIR, "Infos.txt")

with open(INFOS_PATH, "r", encoding="utf-8") as f:
    problems = json.load(f)


def populate_database_with_questions(db_name="database.db",num_instances=50):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    for _ in range(num_instances):
        variables, domains, constraints, partial_assignment = generate_random_csp()
        question_text = generate_csp_question_text(
            variables, domains, constraints, partial_assignment
        )

        cursor.execute(
            "INSERT INTO csp_questions (question_text) VALUES (?)",
            (question_text,)
        )

    conn.commit()
    conn.close()



DB_PATH = "database.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS SmartQuestionsStrategii (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    KeyWords TEXT,
    Lenght INTEGER,
    HelWords TEXT
)
""")

cursor.execute("DROP TABLE IF EXISTS SmartTemplates")
cursor.execute("""
CREATE TABLE SmartTemplates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Words TEXT NOT NULL,
    Instances TEXT NOT NULL,
    RightWord TEXT NOT NULL
)
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        algorithm TEXT NOT NULL,
        question_text TEXT NOT NULL,
        graph TEXT NOT NULL,
        start_node TEXT NOT NULL,
        goal_node TEXT NOT NULL,
        heuristic TEXT,
        costs TEXT
    )
    """)
cursor.execute("DROP TABLE IF EXISTS QuestionsAnswers")
cursor.execute("""
CREATE TABLE QuestionsAnswers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Question TEXT NOT NULL,
    Answer TEXT NOT NULL,
    Capitol TEXT NOT NULL
)
""")
cursor.execute("""
        CREATE TABLE IF NOT EXISTS csp_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL
        )
    """)


cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_qa_question ON QuestionsAnswers(Question);")
cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_templates_pair ON SmartTemplates(Words, Instances);")

with open("Infos.txt", "r", encoding="utf-8") as f:
    problems = json.load(f)

all_pairs = []
for problem, info in problems.items():
    strategy = info["strategy"]
    for instance in info["instances"]:
        all_pairs.append((problem, instance, strategy))

k = min(50, len(all_pairs))
picked = random.sample(all_pairs, k)

qa_data = []
for problem, instance, strategy in picked:
    question = f"Care este strategia de rezolvare pentru problema {problem} și care are instanța {instance}?"
    answer = f"Strategia de rezolvare pentru problema {problem} și instanța {instance} este {strategy}."
    qa_data.append((question, answer, "Capitol I-III"))

cursor.executemany(
    "INSERT OR IGNORE INTO QuestionsAnswers (Question, Answer, Capitol) VALUES (?, ?, ?)",
    qa_data
)

template_data = []
for problem, instance, strategy in all_pairs:
    template_data.append((problem, instance, strategy))

cursor.executemany(
    "INSERT OR IGNORE INTO SmartTemplates (Words, Instances, RightWord) VALUES (?, ?, ?)",
    template_data
)

cursor.execute("""
CREATE TABLE IF NOT EXISTS GameModels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    NumPlayers INTEGER,
    Strategies TEXT,
    Payoffs TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS GameQuestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    GameID INTEGER,
    Question TEXT,
    Answer TEXT,
    FOREIGN KEY (GameID) REFERENCES GameModels(id)
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS bayes_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_text TEXT NOT NULL
)
""")

for _ in range(20):
    players = random.randint(2, 3)
    strategies, payoffs = generate_random_game(players)

    cursor.execute(
        "INSERT INTO GameModels (NumPlayers, Strategies, Payoffs) VALUES (?, ?, ?)",
        (players, json.dumps(strategies), json.dumps(payoffs))
    )
    game_id = cursor.lastrowid

    question = f"Are următorul joc (ID {game_id}) un echilibru Nash pur?"
    cursor.execute(
        "INSERT INTO GameQuestions (GameID, Question, Answer) VALUES (?, ?, ?)",
        (game_id, question, "NEDETERMINAT")
    )

print("✔ 20 jocuri random inserate.")

for strategies, payoffs in hardcoded_games():
    cursor.execute(
        "INSERT INTO GameModels (NumPlayers, Strategies, Payoffs) VALUES (?, ?, ?)",
        (2, json.dumps(strategies), json.dumps(payoffs))
    )
    gid = cursor.lastrowid

    cursor.execute(
        "INSERT INTO GameQuestions (GameID, Question, Answer) VALUES (?, ?, ?)",
        (gid,
         f"Are următorul joc (ID {gid}) un echilibru Nash pur?",
         "DA, jocul are cel puțin un echilibru Nash pur.")
    )

conn.commit()
conn.close()

print("✔ 5 jocuri hardcoded cu Nash pur inserate.")
print(f"✔ {len(qa_data)} întrebări Smart au fost generate (fără duplicate) pentru QuestionsAnswers.")
print(f"✔ {len(template_data)} template-uri au fost generate pentru SmartTemplates.")

populate_database_with_questions()
populate_search_questions()
populate_bayes_questions()