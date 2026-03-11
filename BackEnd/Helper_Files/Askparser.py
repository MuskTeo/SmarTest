import re
import difflib
from Rules_Template_Q1 import get_right_strategy
from Nash import explain_nash_analysis
from StrategyDB import STRATEGY_DB


def detect_tip_from_text(text):
    t = text.lower()
    if "nash" in t:
        return "echilibru nash"
    if "strategie optimă" in t or "strategia optimă" in t or "optim" in t:
        return "strategie optima"
    return "necunoscut"


def match_template_question(text, cursor):
    row = cursor.execute(
        "SELECT Answer FROM QuestionsAnswers WHERE lower(Question)=lower(?)",
        (text.strip(),)
    ).fetchone()
    if row:
        return row["Answer"]
    return None


def fuzzy_contains(word, text):
    words = text.lower().split()
    close = difflib.get_close_matches(word.lower(), words, n=1, cutoff=0.7)
    return len(close) > 0


def detect_strategy_problem(text):
    t = text.lower()

    for canonical_name, info in STRATEGY_DB.items():
        for kw in info["keywords"]:
            if kw in t:
                return canonical_name
            for w in kw.split():
                if fuzzy_contains(w, t):
                    return canonical_name

    return None


def detect_strategy_instance(text):
    t = text.lower()

    m = re.search(r"(\d+)\s*regine", t)
    if m:
        return f"{m.group(1)} regine"

    m = re.search(r"(\d+)\s*(bețe|bete|tije).*?(\d+)\s*discuri", t)
    if m:
        return f"{m.group(1)} bețe și {m.group(3)} discuri"

    m = re.search(r"(\d+)\s*x\s*(\d+)", t)
    if m:
        return f"tablă {m.group(1)}x{m.group(2)}"

    m = re.search(r"graf.*?(\d+)\s*nod", t)
    if m:
        return f"graf cu {m.group(1)} noduri"

    return "instanță necunoscută"


def build_strategy_response(problem, instance):
    strategy = STRATEGY_DB[problem]["strategy"]
    templates = [
        f"Strategia optimă este: {strategy}\nInstanță detectată: {instance}",
        f"Răspuns: strategia corectă este {strategy}.\n(Instanță: {instance})",
        f"Analiza indică strategia optimă: {strategy}.\nInstanța recunoscută: {instance}",
        f"Pentru această configurație, metoda optimă este {strategy}.\nInstanță: {instance}"
    ]
    import random
    return random.choice(templates)


def parse_game_from_text(text):
    text = text.replace("\n", " ").replace("\t", " ")

    players = []
    strategies = []

    player_regex = re.findall(
        r"([A-Za-zȘșȚțĂăÂâÎî]+)\s+poate\s+alege\s*:\s*\[(.*?)\]",
        text
    )

    for name, block in player_regex:
        strat_list = re.split(r"[;,]", block)
        strat_list = [s.strip().strip("'").strip('"') for s in strat_list if s.strip()]
        players.append(name)
        strategies.append(strat_list)

    payoff_dict = {}

    pattern = re.findall(
        r"\(?\s*(\d+\s*,\s*\d+)\s*\)?\s*(?:→|->|=>|:)?\s*.*?Payoff\s*[:=]?\s*\[(.*?)\]",
        text
    )

    for combo_raw, payoff_raw in pattern:
        combo = tuple(int(x.strip()) for x in combo_raw.split(","))
        payoff = [int(x.strip()) for x in payoff_raw.split(",")]
        payoff_dict[combo] = payoff

    if not payoff_dict:
        loose = re.findall(
            r"\(?\s*(\d+\s*,\s*\d+)\s*\)?\s*(?:→|->|=>)?\s*.*?\[(\d+\s*,\s*\d+)\]",
            text
        )
        for combo_raw, payoff_raw in loose:
            combo = tuple(int(x.strip()) for x in combo_raw.split(","))
            payoff = [int(x.strip()) for x in payoff_raw.split(",")]
            payoff_dict[combo] = payoff

    return players, strategies, payoff_dict


def build_nash_response(parsed_game):
    players, strategies, payoff_dict = parsed_game
    num_players = len(players)
    return explain_nash_analysis(strategies, payoff_dict, num_players)

