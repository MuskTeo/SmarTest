import random
import re

from itertools import product
def _clean(s: str) -> str:
    return (s or "").strip().lower()
STRATEGY_WORDS = [
    "Atac cu Sabia", "Blocaj", "Magie", "Eschivă", "Săgeată Rapidă", "Scut Magic",
    "Contraatac", "Lovitură Puternică", "Teleportare", "Camuflaj", "Aruncare Cuțit",
    "Foc", "Gheață", "Fulger", "Vrajă Vindecare", "Atac Aerian", "Zbor", "Rulare",
    "Furtună", "Control Minte", "Lovitură Întunecată", "Atac Sonic", "Strivire",
    "Săritură", "Kick", "Pumn Rapid", "Lansare Suliță", "Vortex", "Invocare Lup",
    "Atac Toxic"
]

PLAYER_NAMES = [
    "Andrei", "Bianca", "Cristi", "Daria", "Elena", "Flaviu", "George", "Horia",
    "Iulia", "Larisa", "Mihai", "Nadia", "Ovidiu", "Paula", "Radu", "Sonia",
    "Tudor", "Vlad"
]


def humanize_strategies(strategies):
    players = random.sample(PLAYER_NAMES, len(strategies))
    human_map = []

    for i, strat_list in enumerate(strategies):
        names = random.sample(STRATEGY_WORDS, len(strat_list))
        human_map.append((players[i], names))

    return human_map


def _parse_combo_key(key):
    """
    Acceptă:
      - tuple: (0,1) / (0,1,2)
      - string: "(0, 1)", "(0,1)", "0,1", "[0,1]", "(0,1,2)" etc.
    Returnează tuple[int,...] sau None.
    """
    if isinstance(key, tuple):
        return tuple(int(x) for x in key)

    if not isinstance(key, str):
        return None

    nums = re.findall(r"-?\d+", key)
    if not nums:
        return None
    return tuple(int(x) for x in nums)


def normalize_payoffs(payoffs):
    """
    Returnează dict: profile(tuple) -> payoff_vec(list/tuple)
    Suportă:
      - dict cu chei "(i, j)" sau "(i,j,k)" etc.
      - matrice 2D (list-of-lists) pentru 2 jucători: payoffs[i][j] = [p1,p2]
    """
    norm = {}

    # matrice 2D (2 jucători)
    if isinstance(payoffs, list):
        for i, row in enumerate(payoffs):
            if not isinstance(row, list):
                continue
            for j, cell in enumerate(row):
                norm[(i, j)] = cell
        return norm

    # dict
    if isinstance(payoffs, dict):
        for k, v in payoffs.items():
            combo = _parse_combo_key(k)
            if combo is None:
                continue
            norm[combo] = v
        return norm

    return norm


def format_game_for_question(strategies, payoffs_dict):
    human = humanize_strategies(strategies)
    num_players = len(strategies)

    pay = normalize_payoffs(payoffs_dict)

    text = "Jucători și strategii:\n"
    for name, strat_names in human:
        text += f"  {name} poate alege: {strat_names}\n"
    text += "\n"

    if num_players == 2:
        p1_name, p1_strats = human[0]
        p2_name, p2_strats = human[1]

        text += "Reprezentare matriceală pentru jocul cu 2 jucători:\n\n"
        text += f"          {p2_name}:\n"
        text += "              " + " | ".join(f"{s[:10]:<10}" for s in p2_strats) + "\n"
        text += "            " + "-" * (14 + 14 * len(p2_strats)) + "\n"

        for i, strat1 in enumerate(p1_strats):
            row = f"{p1_name[:10]:<10} {strat1[:10]:<10} | "
            for j, strat2 in enumerate(p2_strats):
                payoff = pay.get((i, j), [0, 0])
                row += f"{tuple(payoff)}   "
            text += row + "\n"

        text += "\n"
        return text

    text += "Payoff-uri pentru combinații:\n"
    for combo, payoff in pay.items():
        # mapăm combo -> nume strategii
        readable = []
        for p in range(num_players):
            idx = combo[p] if p < len(combo) else 0
            idx = max(0, min(idx, len(human[p][1]) - 1))
            readable.append(human[p][1][idx])

        text += f"  Combinația {combo} → {readable}\n"
        text += f"     Payoff: {payoff}\n"

    return text


def get_nash_pure_equilibria(strategies, payoffs, num_players=None):
    """
    Pure Nash equilibria pentru N jucători.
    Returnează lista de profile (tuple de indici) care sunt echilibre Nash pure.
    """
    if num_players is None:
        num_players = len(strategies)

    pay = normalize_payoffs(payoffs)

    sizes = [len(strategies[p]) for p in range(num_players)]
    if any(s <= 0 for s in sizes):
        return []

    equilibria = []

    # iterăm toate profilele posibile (i,j) / (i,j,k) ...
    for profile in product(*[range(s) for s in sizes]):
        if profile not in pay:
            continue

        vec = pay[profile]
        if not isinstance(vec, (list, tuple)) or len(vec) < num_players:
            continue

        is_nash = True

        for p in range(num_players):
            current = vec[p]
            best = current

            # devieri unilaterale
            for alt in range(sizes[p]):
                if alt == profile[p]:
                    continue
                new_profile = list(profile)
                new_profile[p] = alt
                new_profile = tuple(new_profile)

                if new_profile not in pay:
                    continue

                new_vec = pay[new_profile]
                if not isinstance(new_vec, (list, tuple)) or len(new_vec) < num_players:
                    continue

                if new_vec[p] > best:
                    best = new_vec[p]
                    break

            if best > current:
                is_nash = False
                break

        if is_nash:
            equilibria.append(profile)

    return equilibria


def explain_nash_analysis(strategies, payoffs, num_players=None):
    """
    Explicație (verbose) pentru Nash pur, bazată pe normalizare.
    """
    if num_players is None:
        num_players = len(strategies)

    pay = normalize_payoffs(payoffs)
    sizes = [len(strategies[p]) for p in range(num_players)]

    explanation = []
    explanation.append("=== Analiză pentru echilibrul Nash pur ===\n")

    # ordonăm profilele ca să fie stabil output-ul
    profiles = sorted(pay.keys())

    for profile in profiles:
        vec = pay[profile]
        if not isinstance(vec, (list, tuple)) or len(vec) < num_players:
            continue

        explanation.append(f"• Profil {profile}")
        explanation.append(f"    Payoff: {list(vec)}")

        is_nash = True

        for p in range(num_players):
            current = vec[p]
            explanation.append(f"    Jucătorul {p+1} (strategie: {profile[p]}), payoff curent: {current}")

            profitable = False
            for alt in range(sizes[p]):
                if alt == profile[p]:
                    continue

                new_profile = list(profile)
                new_profile[p] = alt
                new_profile = tuple(new_profile)

                if new_profile not in pay:
                    continue

                new_vec = pay[new_profile]
                if not isinstance(new_vec, (list, tuple)) or len(new_vec) < num_players:
                    continue

                new_payoff = new_vec[p]
                tag = "(mai mare)" if new_payoff > current else "(mai mic sau egal)"
                explanation.append(f"      → Deviere {profile[p]} → {alt}: payoff devine {new_payoff} {tag}")

                if new_payoff > current:
                    profitable = True
                    break

            if profitable:
                explanation.append(f"      Deviere profitabilă → NU este Nash (jucătorul {p+1}).")
                is_nash = False
                break
            else:
                explanation.append(f"      Nicio deviere profitabilă pentru jucătorul {p+1}.")

        if is_nash:
            explanation.append(f"    Concluzie: {profile} ESTE echilibru Nash pur.\n")
        else:
            explanation.append(f"    Concluzie: {profile} NU este echilibru Nash pur.\n")

    eq = get_nash_pure_equilibria(strategies, payoffs, num_players)

    explanation.append("=== Rezultatul final ===")
    if not eq:
        explanation.append("Jocul NU are echilibru Nash pur.")
    else:
        explanation.append(f"Echilibre Nash pure găsite: {eq}")

    return "\n".join(explanation)
# --- Nash scoring helpers ---

_TUPLE_RE = re.compile(r"\((\s*-?\d+\s*(?:,\s*-?\d+\s*)+)\)")

def _parse_equilibria_from_text(text: str):
    """
    Extrage tupluri de tip (0, 0, 2) din răspunsul userului.
    Acceptă și texte de gen:
      'Echilibre Nash: [(0, 0, 2), (1,0,0)]'
      'Echilibre: (0,0,2) si (1, 0, 0)'
    """
    s = (text or "").strip()
    out = set()

    for m in _TUPLE_RE.finditer(s):
        inside = m.group(1)
        parts = [p.strip() for p in inside.split(",")]
        if not parts:
            continue
        if any(not re.fullmatch(r"-?\d+", p) for p in parts):
            continue
        out.add(tuple(int(p) for p in parts))

    return out

def _user_says_yes(u: str) -> bool:
    u = _clean(u)
    return any(w in u for w in ["da", "are", "exista", "există", "este", "se gaseste", "se găsește", "gasim", "găsim"])

def _user_says_no(u: str) -> bool:
    u = _clean(u)
    return any(w in u for w in ["nu", "n-are", "nu are", "nu exista", "nu există", "niciun", "nici unul", "fara", "fără"])

def _f1(precision: float, recall: float) -> float:
    if precision <= 0.0 or recall <= 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)

def _score_nash_answer(user_text: str, true_eq_list, num_players: int, strategy_sizes=None) -> float:
    true_set = set(tuple(x) for x in (true_eq_list or []))
    user_set = _parse_equilibria_from_text(user_text)

    u_clean = _clean(user_text)

    # 0) nu da puncte pe răspuns gol / aproape gol
    if len(u_clean) < 2:
        return 0.0

    has_true = len(true_set) > 0

    # 1) filtrăm tuplurile userului (ca să nu confundăm payoff-uri cu echilibre)
    if strategy_sizes:
        filtered = set()
        for t in user_set:
            if len(t) != num_players:
                continue
            ok = True
            for p in range(num_players):
                if t[p] < 0 or t[p] >= strategy_sizes[p]:
                    ok = False
                    break
            if ok:
                filtered.add(t)
        user_set = filtered
    else:
        # măcar filtrăm pe dimensiune
        user_set = {t for t in user_set if len(t) == num_players}

    u_yes = _user_says_yes(user_text)
    u_no = _user_says_no(user_text)
    inferred_yes = len(user_set) > 0

    # 2) existență (40%)
    existence_score = 0.0

    if has_true:
        if (u_yes or inferred_yes) and not u_no:
            existence_score = 1.0
        elif u_no and not (u_yes or inferred_yes):
            existence_score = 0.0
        else:
            # contradictoriu (ex: "nu" + listă tupluri) → parțial
            existence_score = 0.4
    else:
        # nu există Nash → cerem explicit "nu"/"fără"/"nu există"
        if u_no and not (u_yes or inferred_yes):
            existence_score = 1.0
        elif u_yes or inferred_yes:
            existence_score = 0.0
        else:
            existence_score = 0.0  # fără afirmație clară, nu dăm puncte

    # 3) echilibre (60%) — F1
    if not has_true:
        equilibria_score = 1.0 if len(user_set) == 0 else 0.0
    else:
        if len(user_set) == 0:
            equilibria_score = 0.0
        else:
            inter = true_set & user_set
            precision = len(inter) / max(1, len(user_set))
            recall = len(inter) / max(1, len(true_set))
            equilibria_score = _f1(precision, recall)

    total = 0.4 * existence_score + 0.6 * equilibria_score
    return max(0.0, min(total, 1.0))