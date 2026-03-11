from flask import Blueprint, jsonify, request
import sqlite3
import sys, os, json, re
import random
import math
from difflib import SequenceMatcher

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Helper_Files')))
from Rules_Template_Q1 import *
from Csp_solver import get_csp_answer_from_text
from Csp_parser import parse_csp_question_text
from csp_scoring import *
from Restrictions import solve_csp_fc
from Nash import explain_nash_analysis, get_nash_pure_equilibria, format_game_for_question,_score_nash_answer
from csp_util import parse_user_assignment
from Nashsolver import *
from Askparser import *
from StrategyDB import *
from Graphsolver import *
from Bayessolver import *

api = Blueprint("api", __name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "Database", "database.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _clean(s: str) -> str:
    return (s or "").strip().lower()

def _sim(a: str, b: str) -> float:
    a = _clean(a)
    b = _clean(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

def _tokens(s: str):
    return set(re.findall(r"[a-zăâîșț0-9]+", (s or "").lower()))

STOP = {
    "strategia", "strategie", "este", "cu", "pentru",
    "optima", "optimă", "instanta", "instanța", "instanţa",
    "problema", "care", "ce", "unui", "unei", "si", "și", "are"
}

TOKEN_RE_MM = re.compile(r"""
    \s*(
        MAX|MIN|
        \(|\)|,|
        -?\d+(?:\.\d+)?
    )
""", re.VERBOSE | re.IGNORECASE)

def tokenize_strict_mm(s: str):
    tokens = []
    pos = 0
    for m in TOKEN_RE_MM.finditer(s):
        if m.start() != pos:
            bad = s[pos:m.start()]
            if bad.strip():
                raise ValueError(f"Caractere invalide în input: {bad!r}")
        tokens.append(m.group(1).upper())
        pos = m.end()
    if pos != len(s) and s[pos:].strip():
        raise ValueError(f"Caractere invalide la final: {s[pos:]!r}")
    if not tokens:
        raise ValueError("Input gol sau invalid.")
    return tokens

class ParserMM:
    def __init__(self, tokens):
        self.t = tokens
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def eat(self, expected=None):
        tok = self.peek()
        if tok is None:
            raise ValueError("Sfârșit neașteptat de input.")
        if expected is not None and tok != expected:
            raise ValueError(f"Așteptam {expected}, am găsit {tok}.")
        self.i += 1
        return tok

    def parse_expr(self):
        tok = self.peek()
        if tok in ("MAX", "MIN"):
            node_type = self.eat()
            self.eat("(")
            children = [self.parse_expr()]
            while self.peek() == ",":
                self.eat(",")
                children.append(self.parse_expr())
            self.eat(")")
            return {"type": node_type, "children": children}
        num = self.eat()
        return {"value": float(num) if "." in num else int(num)}

def parse_tree_mm(expr: str):
    tokens = tokenize_strict_mm(expr)
    p = ParserMM(tokens)
    tree = p.parse_expr()
    if p.peek() is not None:
        raise ValueError(f"Token neconsumat la final: {p.peek()}")
    return tree

def alphabeta_mm(node, alpha=-math.inf, beta=math.inf):
    if "value" in node:
        return node["value"], 1

    visited = 0

    if node["type"] == "MAX":
        value = -math.inf
        for ch in node["children"]:
            child_val, child_vis = alphabeta_mm(ch, alpha, beta)
            visited += child_vis
            value = max(value, child_val)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, visited

    value = math.inf
    for ch in node["children"]:
        child_val, child_vis = alphabeta_mm(ch, alpha, beta)
        visited += child_vis
        value = min(value, child_val)
        beta = min(beta, value)
        if alpha >= beta:
            break
    return value, visited

def extract_expr_mm(text: str):
    m = re.search(r"\b(MAX|MIN)\s*\(", text, flags=re.IGNORECASE)
    if not m:
        return None
    s = text[m.start():].strip()
    depth = 0
    end = None
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    return s[:end] if end else None

def solve_minmax_mm(expr_or_text: str):
    expr = (expr_or_text or "").strip()
    tree = parse_tree_mm(expr)
    return alphabeta_mm(tree)

def mm_generate_tree(height: int, node_type: str = "MAX", lo: int = -9, hi: int = 9, branching: int = 2):
    if height <= 1:
        return {"value": random.randint(lo, hi)}
    next_type = "MIN" if node_type == "MAX" else "MAX"
    return {"type": node_type, "children": [mm_generate_tree(height - 1, next_type, lo, hi, branching) for _ in range(branching)]}

def mm_tree_to_expr(node) -> str:
    if "value" in node:
        v = node["value"]
        if isinstance(v, float) and float(v).is_integer():
            v = int(v)
        return str(v)
    inner = ",".join(mm_tree_to_expr(ch) for ch in node["children"])
    return f"{node['type']}({inner})"

def mm_make_questions(count: int, height: int, lo: int = -9, hi: int = 9, branching: int = 2):
    qlist = []
    for i in range(count):
        tree = mm_generate_tree(height=height, node_type="MAX", lo=lo, hi=hi, branching=branching)
        expr = mm_tree_to_expr(tree)
        root_val, leaves = alphabeta_mm(tree)

        q_text = (
            "Pentru arborele dat, care va fi valoarea din rădăcină și câte noduri frunze vor fi vizitate "
            "în cazul aplicării strategiei MinMax cu optimizarea Alpha-Beta?\n\n"
            f"{expr}"
        )
        ans = f"Valoarea din rădăcină: {root_val}\nFrunze vizitate (Alpha-Beta): {leaves}"

        qlist.append({"id": i + 1, "text": q_text, "answer": ans, "type": "minmax", "expr": expr})
    return qlist

def mm_pick_height():
    return random.choice([3, 4])

def parse_user_minmax_answer(s: str):
    nums = [int(x) for x in re.findall(r"-?\d+", (s or ""))]
    if not nums:
        return None, None
    if len(nums) == 1:
        return nums[0], None
    return nums[0], nums[1]

def _norm_model(m: str) -> str:
    m = _clean(m)
    if not m:
        return "template"
    if "template" in m:
        return "template"
    if m in {"ml", "rn", "optim", "optim-mode", "optimmode"}:
        return "optim-mode"
    if "alpha" in m or "beta" in m or "alphabeta" in m:
        return "alphabeta"
    return m


def _norm_tip(t: str, q: str = "") -> str:
    t = _clean(t)
    ql = _clean(q)

    if "mix" in t or "all" in t or "toate" in t:
        return "mix"

    if "minmax" in t or "minimax" in t or "alphabeta" in t or "alpha" in t or "beta" in t:
        return "minmax"
    if "max(" in ql or "min(" in ql:
        return "minmax"

    if "asign" in t or "csp" in t or "asign" in ql:
        return "asignari"

    if "nash" in t or "echilibru" in t or "nash" in ql:
        return "echilibru nash"

    if "strategie" in t or "optima" in t or "curs" in t or "capitol" in t:
        return "strategie optima"
    if "search" in t:
        return "search"
    if "bayes" in t:
        return "bayes"

    return "strategie optima"
def _build_mix_test(cursor, model: str, total: int = 10):
    questions = []

    n_minmax = 2
    n_csp = 3
    n_nash = 2
    n_opt = total - (n_minmax + n_csp + n_nash)

    # --- MINMAX (generate)
    height = mm_pick_height()
    questions.extend(mm_make_questions(count=n_minmax, height=height, lo=-9, hi=9, branching=2))

    # --- CSP (din DB)
    rows = cursor.execute(
        "SELECT id, question_text FROM csp_questions ORDER BY RANDOM() LIMIT ?",
        (n_csp,)
    ).fetchall()

    for r in rows:
        qt = r["question_text"]
        questions.append({
            "id": r["id"],
            "text": qt,
            "answer": get_csp_answer_from_text(qt),
            "type": "asignari"
        })

    # --- NASH (din DB)
    rows = cursor.execute(
        "SELECT id, GameID FROM GameQuestions ORDER BY RANDOM() LIMIT ?",
        (n_nash,)
    ).fetchall()

    for r in rows:
        game_id = r["GameID"]
        gm = cursor.execute("SELECT * FROM GameModels WHERE id=?", (game_id,)).fetchone()
        if not gm:
            continue

        strategies = json.loads(gm["Strategies"])
        payoffs = json.loads(gm["Payoffs"])
        num_players = gm["NumPlayers"]

        eq = get_nash_pure_equilibria(strategies, payoffs, num_players)
        pretty_game = format_game_for_question(strategies, payoffs)
        question_text = f"Are următorul joc (ID {game_id}) un echilibru Nash pur?\n\n{pretty_game}"
        ans = "Jocul NU are echilibru Nash pur." if not eq else f"Echilibre Nash pure găsite: {eq}"

        questions.append({
            "id": r["id"],
            "game_id": game_id,
            "text": question_text,
            "answer": ans,
            "type": "nash"
        })

    # --- STRATEGIE OPTIMĂ
    if model == "template":
        rows = cursor.execute(
            "SELECT * FROM QuestionsAnswers ORDER BY RANDOM() LIMIT ?",
            (n_opt,)
        ).fetchall()

        for r in rows:
            questions.append({
                "id": r["id"],
                "text": r["Question"],
                "answer": r["Answer"],
                "type": "optima"
            })
    else:
        rows = cursor.execute(
            "SELECT id, Words, Instances FROM SmartTemplates ORDER BY RANDOM() LIMIT ?",
            (n_opt,)
        ).fetchall()

        for r in rows:
            right = get_right_strategy(r["Words"], r["Instances"])
            questions.append({
                "id": r["id"],
                "text": f"Care este strategia optimă pentru {r['Words']} (instanța {r['Instances']})?",
                "answer": right,
                "type": "optima"
            })

    random.shuffle(questions)
    return questions

@api.route("/smartest/test", methods=["GET"])
def get_test():
    tip_raw = request.args.get("tip", "")
    model_raw = request.args.get("model", "")

    tip = _norm_tip(tip_raw)
    model = _norm_model(model_raw)

    conn = get_db_connection()
    cursor = conn.cursor()

    if tip == "mix":
        questions = _build_mix_test(cursor, model=model, total=10)
        conn.close()
        return jsonify({"questions": questions})

    if tip == "minmax":
        height = mm_pick_height()
        questions = mm_make_questions(count=10, height=height, lo=-9, hi=9, branching=2)
        conn.close()
        return jsonify({"questions": questions})

    if tip == "asignari":
        rows = cursor.execute(
            "SELECT id, question_text FROM csp_questions ORDER BY RANDOM() LIMIT 10"
        ).fetchall()

        questions = []
        for r in rows:
            qt = r["question_text"]
            questions.append({
                "id": r["id"],
                "text": qt,
                "answer": get_csp_answer_from_text(qt),
                "type": "asignari"
            })

        conn.close()
        return jsonify({"questions": questions})

    if tip == "echilibru nash":
        rows = cursor.execute("SELECT * FROM GameQuestions ORDER BY RANDOM() LIMIT 10").fetchall()
        questions = []
        for r in rows:
            game_id = r["GameID"]
            gm = cursor.execute("SELECT * FROM GameModels WHERE id=?", (game_id,)).fetchone()
            if not gm:
                continue

            strategies = json.loads(gm["Strategies"])
            payoffs_dict = json.loads(gm["Payoffs"])
            num_players = gm["NumPlayers"]

            answer = r["Answer"] if model == "template" else explain_nash_analysis(strategies, payoffs_dict, num_players)
            pretty_game = format_game_for_question(strategies, payoffs_dict)
            question_text = f"Are următorul joc (ID {game_id}) un echilibru Nash pur?\n\n{pretty_game}"

            questions.append({
                "id": r["id"],
                "game_id": game_id,
                "text": question_text,
                "answer": answer,
                "type": "nash"
            })

        conn.close()
        return jsonify({"questions": questions})

    if tip == "strategie optima" and model == "template":
        rows = cursor.execute("SELECT * FROM QuestionsAnswers ORDER BY RANDOM() LIMIT 10").fetchall()
        conn.close()
        return jsonify({"questions": [
            {"id": r["id"], "text": r["Question"], "answer": r["Answer"], "type": "optima"} for r in rows
        ]})

    if tip == "strategie optima" and model != "template":
        rows = cursor.execute("SELECT id, Words, Instances FROM SmartTemplates ORDER BY RANDOM() LIMIT 10").fetchall()
        conn.close()
        questions = []
        for r in rows:
            strat = get_right_strategy(r["Words"], r["Instances"])
            questions.append({
                "id": r["id"],
                "text": f"Care este strategia optimă pentru {r['Words']} (instanța {r['Instances']})?",
                "answer": strat,
                "type": "optima"
            })
        return jsonify({"questions": questions})

    conn.close()
    return jsonify({"questions": []})
@api.route("/smartest/question", methods=["GET"])
def get_questions_by_filter():
    count = request.args.get("count", 5, type=int)
    tip_raw = request.args.get("tip", "")
    model_raw = request.args.get("model", "")

    tip = _norm_tip(tip_raw)
    model = _norm_model(model_raw)
    conn = get_db_connection()

    cursor = conn.cursor()
    if tip == "minmax":
        height = mm_pick_height()
        qlist = mm_make_questions(count=count, height=height, lo=-9, hi=9, branching=2)
        conn.close()
        return jsonify({"questions": qlist})
    if tip == "bayes":
     rows = cursor.execute(
        "SELECT id, question_text FROM bayes_questions ORDER BY RANDOM() LIMIT ?",
        (count,)
     ).fetchall()

     qlist = []
     for r in rows:
        PA, PB_A, PB_notA, PC_B, PC_notB = parse_bayes_question(r["question_text"])
        value = solve_bayes_chain(PA, PB_A, PB_notA, PC_B, PC_notB)

        qlist.append({
            "id": r["id"],
            "text": r["question_text"],
            "answer": f"P(C) ≈ {value}",
            "type": "bayes"
        })

     conn.close()
     return jsonify({"questions": qlist})
    if tip == "search":
     rows = cursor.execute(
        "SELECT id, question_text FROM search_questions ORDER BY RANDOM() LIMIT ?",
        (count,)
     ).fetchall()

     qlist = []
     for r in rows:
        # parse din TEXT
        problem = parse_search_question_text(r["question_text"])

        # rezolvare
        correct_path = solve_search_problem(problem)

        qlist.append({
            "id": r["id"],
            "text": r["question_text"],
            "answer": (
                " → ".join(correct_path)
                if correct_path else
                "Nu există drum între starea inițială și cea finală."
            ),
            "type": "search"
        })

     conn.close()
     return jsonify({"questions": qlist})
    if tip == "asignari":
     rows = cursor.execute(
        "SELECT id, question_text FROM csp_questions ORDER BY RANDOM() LIMIT ?",
        (count,)
        ).fetchall()

    qlist = []
    for r in rows:
        qt = r["question_text"]
        qlist.append({
            "id": r["id"],
            "text": qt,
            "answer": get_csp_answer_from_text(qt),
            "type": "asignari"
        })

        conn.close()
        return jsonify({"questions": qlist})
    if tip == "echilibru nash":
        rows = cursor.execute("SELECT * FROM GameQuestions ORDER BY RANDOM() LIMIT ?", (count,)).fetchall()
        qlist = []
        for r in rows:
            game_id = r["GameID"]
            gm = cursor.execute("SELECT * FROM GameModels WHERE id=?", (game_id,)).fetchone()
            strategies = json.loads(gm["Strategies"])
            payoffs_dict = json.loads(gm["Payoffs"])
            num_players = gm["NumPlayers"]

            answer = r["Answer"] if model == "template" else explain_nash_analysis(strategies, payoffs_dict, num_players)
            pretty_game = format_game_for_question(strategies, payoffs_dict)
            question_text = f"Are următorul joc (ID {game_id}) un echilibru Nash pur?\n\n{pretty_game}"


            qlist.append({
                "id": r["id"],
                "text": question_text,
                "answer": answer,
                "type": "nash"
            })

        conn.close()
        return jsonify({"questions": qlist})

    if tip == "strategie optima" and model == "template":
        rows = cursor.execute("SELECT * FROM QuestionsAnswers ORDER BY RANDOM() LIMIT ?", (count,)).fetchall()
        conn.close()
        return jsonify({"questions": [
            {"id": r["id"], "text": r["Question"], "answer": r["Answer"], "type": "optima"}
            for r in rows
        ]})

    if tip == "strategie optima" and model != "template":
        from Rules_Template_Q1 import get_right_strategy
        rows = cursor.execute("SELECT id, Words, Instances FROM SmartTemplates ORDER BY RANDOM() LIMIT ?", (count,)).fetchall()
        conn.close()
        qlist = []
        for r in rows:
            right = get_right_strategy(r["Words"], r["Instances"])
            qlist.append({
                "id": r["id"],
                "text": f"Care este strategia optimă pentru {r['Words']} (instanța {r['Instances']})?",
                "answer": right,
                "type": "optima"
            })
        return jsonify({"questions": qlist})

    conn.close()
    return jsonify({"questions": []})


@api.route("/smartest/ask", methods=["POST"])
def ask_free_question():
    data = request.get_json(silent=True) or {}
    q_raw = (data.get("question") or "").strip()
    if not q_raw:
        return jsonify({"error": "Întrebarea este goală."}), 400

    model = _norm_model(request.args.get("model") or data.get("model") or "optim-mode")
    tip = _norm_tip(request.args.get("tip") or data.get("tip") or "", q_raw)

    conn = get_db_connection()
    cursor = conn.cursor()

    if tip == "minmax":
        expr = (data.get("expr") or "").strip()
        if not expr:
            expr = extract_expr_mm(q_raw) or ""

        if not expr:
            conn.close()
            return jsonify({"answer": "Scrie arborele în format MAX(...)/MIN(...). Ex: MAX(MIN(3,5),MIN(2,9))"}), 200

        try:
            val, leaves = solve_minmax_mm(expr)
            conn.close()
            return jsonify({"answer": f"Valoarea din rădăcină: {val}\nFrunze vizitate (Alpha-Beta): {leaves}"}), 200
        except Exception as e:
            conn.close()
            return jsonify({"answer": f"Input invalid pentru arbore: {str(e)}"}), 200
    if tip == "strategie optima" and model == "template":
        ans = match_template_question(q_raw, cursor)
        conn.close()
        if ans:
            return jsonify({"answer": ans})
        return jsonify({"answer": "Nu avem un răspuns template pentru această întrebare."})
    if tip == "bayes":
     PA, PB_A, PB_notA, PC_B, PC_notB = parse_bayes_question(q_raw)
     value = solve_bayes_chain(PA, PB_A, PB_notA, PC_B, PC_notB)

     conn.close()
     return jsonify({
        "answer": f"P(C) = {value}\n"
     }), 200

    if tip == "search":
    # parse din textul introdus de user
     problem = parse_search_question_text(q_raw)

    # rezolvare
     correct_path = solve_search_problem(problem)

     if correct_path is None:
        answer = "Nu există drum între starea inițială și cea finală."
     else:
        answer = "Drumul obținut este: " + " → ".join(correct_path)

     conn.close()
     return jsonify({"answer": answer}), 200
    # ---------------- OPTIM-MODE STRATEGIE ----------------
    if tip == "strategie optima" and model == "optim-mode":
        problem = detect_strategy_problem(q_raw)
        if not problem:
            conn.close()
            return jsonify({"answer": "Nu pot identifica problema matematică / AI."})

        instance = detect_strategy_instance(q_raw)
        ans = build_strategy_response(problem, instance)
        conn.close()
        return jsonify({"answer": ans})

    # ---------------- TEMPLATE NASH ----------------
    if tip == "echilibru nash" and model == "template":
        row = cursor.execute(
            "SELECT Answer FROM GameQuestions WHERE Question = ?",
            (q_raw,)
        ).fetchone()
        conn.close()
        if row:
            return jsonify({"answer": row["Answer"]})
        return jsonify({"answer": "Nu există acest joc în baza de date."})

    # ---------------- OPTIM-MODE NASH ----------------
    if tip == "echilibru nash" and model == "optim-mode":
        players, strategies, payoffs = parse_game_from_text(q_raw)
        if not players or not strategies or not payoffs:
            conn.close()
            return jsonify({"answer": "Nu pot interpreta jocul pentru analiza Nash."})

        ans = build_nash_response((players, strategies, payoffs))
        conn.close()
        return jsonify({"answer": ans})

    if tip == "asignari":

        answer = get_csp_answer_from_text(q_raw)

        conn.close()
        return jsonify({"answer": answer}), 200
    if tip == "search":
    # parse din textul introdus de user
     problem = parse_search_question_text(q_raw)

    # rezolvare
     correct_path = solve_search_problem(problem)

     if correct_path is None:
        answer = "Nu există drum între starea inițială și cea finală."
     else:
        answer = "Drumul obținut este: " + " → ".join(correct_path)

     conn.close()
     return jsonify({"answer": answer}), 200

    if tip == "echilibru nash":
        ql = _clean(q_raw)
        m = re.search(r"\b(?:id|game)\s*(\d+)\b", ql)
        game_id = None

        if m:
            game_id = int(m.group(1))
        else:
            rows = cursor.execute("SELECT id, GameID, Question FROM GameQuestions").fetchall()
            best = None
            best_s = 0.0
            for r in rows:
                s = _sim(q_raw, r["Question"])
                if s > best_s:
                    best_s = s
                    best = r
            if best and best_s >= 0.45:
                game_id = best["GameID"]

        if not game_id:
            conn.close()
            return jsonify({"answer": "Nu pot identifica jocul. Scrie și ID-ul jocului (ex: ID 7)."}), 200

        gm = cursor.execute("SELECT * FROM GameModels WHERE id=?", (game_id,)).fetchone()
        if not gm:
            conn.close()
            return jsonify({"answer": "Nu am găsit jocul în baza de date."}), 200

        strategies = json.loads(gm["Strategies"])
        payoffs_dict = json.loads(gm["Payoffs"])
        num_players = gm["NumPlayers"]

        if model == "template":
            rowq = cursor.execute("SELECT Answer FROM GameQuestions WHERE GameID=?", (game_id,)).fetchone()
            if rowq and rowq["Answer"] and rowq["Answer"].upper() != "NEDETERMINAT":
                ans = rowq["Answer"]
            else:
                ans = explain_nash_analysis(strategies, payoffs_dict, num_players)
        else:
            ans = explain_nash_analysis(strategies, payoffs_dict, num_players)

        conn.close()
        return jsonify({"answer": ans}), 200

    if model == "template":
        rows = cursor.execute("SELECT Question, Answer FROM QuestionsAnswers").fetchall()
        best_a = None
        best_s = 0.0
        for r in rows:
            s = _sim(q_raw, r["Question"])
            if s > best_s:
                best_s = s
                best_a = r["Answer"]
        conn.close()
        if best_a and best_s >= 0.40:
            return jsonify({"answer": best_a}), 200
        return jsonify({"answer": "Nu am găsit o întrebare suficient de apropiată în QuestionsAnswers."}), 200

    rows = cursor.execute("SELECT Words, Instances, RightWord FROM SmartTemplates").fetchall()
    qt = _tokens(q_raw) - STOP

    best = None
    best_score = 0.0

    inst = None
    m = re.search(r"instan[țt](?:a|ă)\s*([^?)+]+)", q_raw, flags=re.IGNORECASE)
    if m:
        inst = _clean(m.group(1))

    for r in rows:
        if inst:
            if inst not in _clean(r["Instances"]):
                continue
        wt = _tokens(r["Words"]) - STOP
        if not wt:
            continue
        union = qt | wt
        if not union:
            continue
        score = len(qt & wt) / len(union)
        if score > best_score:
            best_score = score
            best = r

    conn.close()

    if not best or best_score < 0.10:
        return jsonify({"answer": "Nu pot identifica problema. Scrie numele (ex: Labirint, 8-puzzle, Knight’s Tour)."}), 200

    return jsonify({"answer": best["RightWord"]}), 200


@api.route("/smartest/raspunsuri", methods=["POST"])
def check_answers():
    data = request.get_json(silent=True) or {}
    user_answers = data.get("answers", [])

    model = _norm_model(request.args.get("model") or data.get("model") or "template")
    tip = _norm_tip(request.args.get("tip") or data.get("tip") or "")

    if not user_answers:
        return jsonify({"score": 0})

    conn = get_db_connection()
    cursor = conn.cursor()

    score_total = 0.0
    matched = 0
    if tip == "mix":
        for ans in user_answers:
            q_text = ans.get("question", "") or ""
            u_text = ans.get("user_answer", "") or ""
            q_type = _clean(ans.get("type", ""))

        # MINMAX
            if q_type == "minmax":
                expr = extract_expr_mm(q_text)
                if not expr:
                    continue
                try:
                    right_val, right_leaves = solve_minmax_mm(expr)
                except:
                    continue

                u_val, u_leaves = parse_user_minmax_answer(u_text)

                local = 0.0
                if u_val is not None and int(u_val) == int(right_val):
                    local += 0.5
                if u_leaves is not None and int(u_leaves) == int(right_leaves):
                    local += 0.5

                score_total += local
                matched += 1
                continue

        # CSP
            if q_type == "asignari":
                variables, domains, constraints, partial = parse_csp_question_text(q_text)
                solution = solve_csp_fc(variables, domains, constraints, partial)

                if solution is None:
                    if any(kw in u_text.lower() for kw in [
                        "nu exista", "nu există", "fara solutie", "fără soluție",
                        "inconsistenta", "inconsistent"
                    ]):
                        score_total += 1.0
                    else:
                        score_total += 0.0
                    matched += 1
                    continue

                user_assign = parse_user_assignment(u_text)
                local = compute_csp_partial_score(user_assign, variables, domains, constraints, partial)
                score_total += local
                matched += 1
                continue

            # NASH
            if q_type == "nash":
                game_id = ans.get("game_id")
                if not game_id:
                    m = re.search(r"\bID\s*(\d+)\b", q_text, flags=re.IGNORECASE)
                    if m:
                        game_id = int(m.group(1))

                if not game_id:
                    continue

                gm = cursor.execute("SELECT * FROM GameModels WHERE id=?", (game_id,)).fetchone()
                if not gm:
                    continue

                strategies = json.loads(gm["Strategies"])
                payoffs = json.loads(gm["Payoffs"])
                num_players = gm["NumPlayers"]
                true_eq = get_nash_pure_equilibria(strategies, payoffs, num_players)

                local = _score_nash_answer(u_text, true_eq, num_players)
                score_total += local
                matched += 1
                continue


        # OPTIMA
            if q_type == "optima":
                if model == "template":
                    row = cursor.execute("SELECT Answer FROM QuestionsAnswers WHERE Question = ?", (q_text,)).fetchone()
                    if not row:
                        continue
                    local = 1.0 if _clean(u_text) == _clean(row["Answer"]) else 0.0
                    score_total += local
                    matched += 1
                else:
                    # optim-mode: folosim SmartTemplates (cautăm după instanță în text)
                    row = cursor.execute(
                        "SELECT Words, Instances FROM SmartTemplates WHERE ? LIKE '%' || Instances || '%'",
                        (q_text,)
                    ).fetchone()
                    if not row:
                        continue
                    right = _clean(get_right_strategy(row["Words"], row["Instances"]))
                    user = _clean(u_text)

                    rt = _tokens(right) - STOP
                    ut = _tokens(user) - STOP
                    hit = len(rt & ut)
                    den = max(1, len(rt))
                    local = (0.2 + 0.8 * (hit / den)) if hit > 0 else 0.15 * _sim(user, right)

                    score_total += max(0.0, min(local, 1.0))
                    matched += 1
                continue

        conn.close()
        if matched == 0:
            return jsonify({"score": 0})
        return jsonify({"score": round((score_total / matched) * 100, 2)})
    if tip == "minmax":
        for ans in user_answers:
            q_text = ans.get("question", "") or ""
            u_text = ans.get("user_answer", "") or ""

            expr = extract_expr_mm(q_text)
            if not expr:
                continue

            try:
                right_val, right_leaves = solve_minmax_mm(expr)
            except:
                continue

            u_val, u_leaves = parse_user_minmax_answer(u_text)

            local = 0.0
            if u_val is not None and int(u_val) == int(right_val):
                local += 0.5
            if u_leaves is not None and int(u_leaves) == int(right_leaves):
                local += 0.5

            # fallback: dacă le-a inversat (rar, dar se întâmplă)
            if local < 1.0 and u_val is not None and u_leaves is not None:
                if int(u_val) == int(right_leaves) and int(u_leaves) == int(right_val):
                    local = 1.0

            score_total += local
            matched += 1

        conn.close()
        if matched == 0:
            return jsonify({"score": 0})
        return jsonify({"score": round((score_total / matched) * 100, 2)})

    if tip == "echilibru nash":
        for ans in user_answers:
            qid = ans.get("id", None)
            q_text = ans.get("question", "")
            u = (ans.get("user_answer", "") or "").strip()

            row = None
            if qid is not None:
                row = cursor.execute("SELECT GameID FROM GameQuestions WHERE id = ?", (qid,)).fetchone()

            if row is None and q_text:
                row = cursor.execute("SELECT GameID FROM GameQuestions WHERE Question = ?", (q_text,)).fetchone()
            if row is None:
                best = cursor.execute("SELECT id, GameID, Question FROM GameQuestions").fetchall()
                best_row = None
                best_s = 0.0
                for br in best:
                    s = _sim(q_text, br["Question"])
                    if s > best_s:
                        best_s = s
                        best_row = br
                if best_row is not None and best_s >= 0.92:
                    row = {"GameID": best_row["GameID"]}

            if not row:
                continue

            gm = cursor.execute("SELECT * FROM GameModels WHERE id=?", (row["GameID"],)).fetchone()
            if not gm:
                continue
            strategies = json.loads(gm["Strategies"])
            payoffs_dict = json.loads(gm["Payoffs"])
            num_players = gm["NumPlayers"]

            # IMPORTANT: ai grijă ca get_nash_pure_equilibria să lucreze cu payoffs_dict (dict normalizat),
            # altfel scorarea va fi corectă, dar "adevărul" (nash_list) va fi greșit.
            nash_list = get_nash_pure_equilibria(strategies, payoffs_dict, num_players)

            matched += 1

            sizes = [len(s) for s in strategies]
            local_score = _score_nash_answer(u, nash_list, num_players, strategy_sizes=sizes)

            score_total += local_score

        conn.close()
        if matched == 0:
            return jsonify({"score": 0})
        return jsonify({"score": round((score_total / matched) * 100, 2)})
    if tip == "asignari":
     for ans in user_answers:
        question_text = ans.get("question", "")
        user_text = ans.get("user_answer", "")

        if not question_text:
            continue

        variables, domains, constraints, partial = \
            parse_csp_question_text(question_text)
        solution = solve_csp_fc(
            variables, domains, constraints, partial
        )

        if solution is None:
            if any(kw in user_text.lower() for kw in [
                "nu exista", "nu există",
                "fara solutie", "fără soluție",
                "inconsistenta", "inconsistent"
            ]):
                local_score = 1.0
            else:
                local_score = 0.0

            score_total += local_score
            matched += 1
            continue
        # parse user assignment
        user_assign = {}
        user_assign = parse_user_assignment(user_text)

        local_score = compute_csp_partial_score(
            user_assign,
            variables,
            domains,
            constraints,
            partial
        )

        score_total += local_score
        matched += 1

     conn.close()
     if matched == 0:
        return jsonify({"score": 0})

     return jsonify({"score": round((score_total / matched) * 100, 2)})


    if tip == "strategie optima" and model == "template":
        for ans in user_answers:
            qid = ans.get("id", None)
            q_text = ans.get("question", "")
            u = _clean(ans.get("user_answer", ""))

            row = None
            if qid is not None:
                row = cursor.execute("SELECT Answer FROM QuestionsAnswers WHERE id = ?", (qid,)).fetchone()
            if row is None and q_text:
                row = cursor.execute("SELECT Answer FROM QuestionsAnswers WHERE Question = ?", (q_text,)).fetchone()

            if not row:
                continue

            matched += 1
            if u == _clean(row["Answer"]):
                score_total += 1.0

        conn.close()
        if matched == 0:
            return jsonify({"score": 0})
        return jsonify({"score": round((score_total / matched) * 100, 2)})
    if tip == "search":
     for ans in user_answers:
        question_text = ans.get("question", "")
        user_text = ans.get("user_answer", "")

        if not question_text:
            continue

        # parse problema
        problem = parse_search_question_text(question_text)

        # soluție corectă
        correct_path = solve_search_problem(problem)

        # CAZ: nu există drum
        if correct_path is None:
            if any(x in user_text.lower() for x in [
                "nu exista", "nu există",
                "fara drum", "fără drum",
                "imposibil"
            ]):
                local_score = 1.0
            else:
                local_score = 0.0

            score_total += local_score
            matched += 1
            continue

        # parse răspuns utilizator
        user_path = parse_user_path(user_text)

        # scor procentual
        local_score = compute_search_score(
            user_path,
            correct_path
        )

        score_total += local_score
        matched += 1

     conn.close()
     if matched == 0:
        return jsonify({"score": 0})

     return jsonify({
        "score": round((score_total / matched) * 100, 2)
     })
    if tip == "bayes":
     for ans in user_answers:
        question_text = ans.get("question", "")
        user_text = ans.get("user_answer", "")

        PA, PB_A, PB_notA, PC_B, PC_notB = parse_bayes_question(question_text)
        correct_value = solve_bayes_chain(PA, PB_A, PB_notA, PC_B, PC_notB)  # float
        user_value = parse_user_numeric_answer(user_text)                    # float|None
 
        local_score = score_bayes_answer(user_value, correct_value, tol=0.02)

        score_total += local_score
        matched += 1

     conn.close()
     return jsonify({"score": round((score_total / matched) * 100, 2)})
    if tip == "strategie optima" and model != "template":
        from Rules_Template_Q1 import get_right_strategy

        for ans in user_answers:
            qid = ans.get("id", None)
            question = ans.get("question", "")
            user = _clean(ans.get("user_answer", ""))

            row = None
            if qid is not None:
                row = cursor.execute("SELECT Words, Instances FROM SmartTemplates WHERE id = ?", (qid,)).fetchone()

            if row is None and question:
                row = cursor.execute(
                    "SELECT Words, Instances FROM SmartTemplates WHERE ? LIKE '%' || Instances || '%'",
                    (question,)
                ).fetchone()

            if not row:
                m = re.search(r"instan[țt]a\s+([^)]+)\)", question, flags=re.IGNORECASE)
                if m:
                    inst = m.group(1).strip()
                    row = cursor.execute("SELECT Words, Instances FROM SmartTemplates WHERE Instances = ?", (inst,)).fetchone()

            if not row:
                continue

            matched += 1

            right = _clean(get_right_strategy(row["Words"], row["Instances"]))

            rt = _tokens(right) - STOP
            ut = _tokens(user) - STOP

            hit = len(rt & ut)
            den = max(1, len(rt))

            if hit > 0:
                local_score = 0.2 + 0.8 * (hit / den)
            else:
                local_score = 0.15 * _sim(user, right)

            if "strategia" in user or "strategie" in user:
                local_score += 0.05
            if "este" in user:
                local_score += 0.03

            if hit == 0 and len(user) < 3:
                local_score -= 0.3

            local_score = max(0.0, min(local_score, 1.0))
            score_total += local_score

        conn.close()
        if matched == 0:
            return jsonify({"score": 0})
        return jsonify({"score": round((score_total / matched) * 100, 2)})

    conn.close()
    return jsonify({"score": 0})
 
