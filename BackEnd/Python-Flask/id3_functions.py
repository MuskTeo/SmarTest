import sqlite3

# === Conectare DB ===
DB_PATH = "database.db"

# === Definim funcțiile de clasificare ===

def classify_nqueens(instance):
    """Arbore decizie pentru N-Queens."""
    if "8" in instance or "10" in instance or "12" in instance:
        return "Backtracking / DFS"
    return "DFS"

def classify_hanoi(instance):
    """Arbore decizie pentru Generalised Hanoi."""
    if "3" in instance or "4" in instance or "5" in instance:
        return "Recursiv / DFS"
    return "DFS"

def classify_graph_coloring(instance):
    """Arbore decizie pentru Graph Coloring."""
    if "complet" in instance or "bipartit" in instance:
        return "Greedy / Heuristică"
    if "graf cu" in instance:
        return "Greedy"
    return "Heuristică"

def classify_knights_tour(instance):
    """Arbore decizie pentru Knight’s Tour."""
    if "5x5" in instance or "6x6" in instance or "8x8" in instance:
        return "DFS cu backtracking"
    return "Backtracking"

def classify_labirint(instance):
    """Arbore decizie pentru Labirint."""
    if "obstacole" in instance:
        return "A*"
    if "dreptunghiular" in instance:
        return "BFS"
    return "A* sau BFS"

def classify_puzzle(instance):
    """Arbore decizie pentru Puzzle-ul celor 8 piese."""
    return "A*"

def classify_hill_climbing(instance):
    """Arbore decizie pentru Hill Climbing Optimization."""
    if "sinusoidală" in instance:
        return "Hill Climbing"
    if "minime locale" in instance:
        return "Hill Climbing (cu restart aleator)"
    return "Hill Climbing"

def classify_planificare_ai(instance):
    """Arbore decizie pentru Planificare AI."""
    return "A*"

def classify_coloring_complex(instance):
    """Arbore decizie pentru Colorarea unui graf complex."""
    if "planar" in instance:
        return "Greedy"
    if "restricții" in instance:
        return "Greedy / Heuristică"
    return "Greedy"

def classify_hanoi_turnuri(instance):
    """Arbore decizie pentru Turnurile din Hanoi."""
    return "Recursiv / DFS"

# === Mapare problemă -> funcție clasificare ===
decision_trees = {
    "N-Queens": classify_nqueens,
    "Generalised Hanoi": classify_hanoi,
    "Graph Coloring": classify_graph_coloring,
    "Knight’s Tour": classify_knights_tour,
    "Labirint": classify_labirint,
    "Puzzle-ul celor 8 piese": classify_puzzle,
    "Hill Climbing Optimization": classify_hill_climbing,
    "Planificare AI": classify_planificare_ai,
    "Colorarea unui graf complex": classify_coloring_complex,
    "Turnurile din Hanoi": classify_hanoi_turnuri,
}

# === Funcție principală care generează strategia potrivită ===
def get_right_strategy(problem, instance):
    if problem not in decision_trees:
        return "Strategie necunoscută"
    return decision_trees[problem](instance)

# === Funcție pentru actualizarea DB-ului cu strategia generată ===
def update_smart_templates():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, Words, Instances FROM SmartTemplates")
    rows = cursor.fetchall()

    updated = 0
    for row in rows:
        id_, words, instance = row
        # identificăm problema după strategie (aproximativ)
        problem = infer_problem_from_strategy(words)
        if not problem:
            continue
        right = get_right_strategy(problem, instance)
        cursor.execute("UPDATE SmartTemplates SET RightWord = ? WHERE id = ?", (right, id_))
        updated += 1

    conn.commit()
    conn.close()
    print(f"✅ {updated} rânduri din SmartTemplates au fost actualizate cu strategiile corecte.")

# === Funcție auxiliară pentru a identifica problema dintr-o strategie ===
def infer_problem_from_strategy(words):
    for problem, func in decision_trees.items():
        if any(keyword in words for keyword in ["DFS", "Greedy", "A*", "Hill Climbing", "Backtracking"]):
            return problem
    return None


if __name__ == "__main__":
    # Test rapid
    print(get_right_strategy("N-Queens", "tablă 8x8"))
    print(get_right_strategy("Labirint", "labirint cu obstacole variabile"))
    update_smart_templates()
 