import random
import string
import sqlite3
import json

def generate_random_graph(num_nodes=5, max_edges=2):
    nodes = list(string.ascii_uppercase[:num_nodes])
    graph = {n: [] for n in nodes}

    for n in nodes:
        neighbors = random.sample(
            nodes,
            random.randint(0, max_edges)
        )
        graph[n] = [v for v in neighbors if v != n]

    start = nodes[0]
    goal = random.choice(nodes[1:])

    return graph, start, goal

def generate_heuristic(nodes):
    return {n: random.randint(0, 5) for n in nodes}

def generate_costs(graph):
    costs = {}
    for u, vs in graph.items():
        for v in vs:
            costs[f"{u}->{v}"] = random.randint(1, 5)
    return costs

def generate_search_question_text(graph, start, goal, algorithm):
    text = "Se consideră următorul graf:\n\n"
    text += "Noduri: " + ", ".join(graph.keys()) + "\n"
    text += "Muchii:\n"

    for u, vs in graph.items():
        for v in vs:
            text += f"{u} → {v}\n"

    text += f"\nStare inițială: {start}\n"
    text += f"Stare scop: {goal}\n\n"
    text += "Cerință:\n"
    text += f"Aplicați algoritmul {algorithm} și indicați drumul găsit.\n"

    return text

def populate_search_questions(db_path="database.db",num_questions=100):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    algorithms = ["BFS", "DFS", "UCS", "GREEDY", "ASTAR"]

    for _ in range(num_questions):
        alg = random.choice(algorithms)
        graph, start, goal = generate_random_graph()

        heuristic = None
        costs = None

        if alg in ("GREEDY", "ASTAR"):
            heuristic = generate_heuristic(graph.keys())

        if alg in ("UCS", "ASTAR"):
            costs = generate_costs(graph)

        question_text = generate_search_question_text(
            graph, start, goal, alg
        )

        cursor.execute(
            """
            INSERT INTO search_questions
            (algorithm, question_text, graph, start_node, goal_node, heuristic, costs)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alg,
                question_text,
                json.dumps(graph),
                start,
                goal,
                json.dumps(heuristic) if heuristic else None,
                json.dumps(costs) if costs else None
            )
        )

    conn.commit()
    conn.close()