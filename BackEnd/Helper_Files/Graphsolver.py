import heapq
import re
from collections import deque

# ======================================================
# PARSER
# ======================================================

def parse_search_question_text(text):
    """
    Returnează un dict:
    {
        "graph": dict[str, list[str]],
        "start": str,
        "goal": str,
        "algorithm": str
    }
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    graph = {}
    start = None
    goal = None
    algorithm = None

    # Noduri
    for l in lines:
        if l.lower().startswith("noduri"):
            nodes = [x.strip() for x in l.split(":")[1].split(",")]
            graph = {n: [] for n in nodes}
            break

    # Muchii
    edges = False
    for l in lines:
        if l.lower().startswith("muchii"):
            edges = True
            continue

        if edges:
            if "→" in l:
                u, v = [x.strip() for x in l.split("→")]
                if u in graph:
                    graph[u].append(v)
            else:
                break

    # Start / Goal
    for l in lines:
        if l.lower().startswith("stare ini"):
            start = l.split(":")[1].strip()
        if l.lower().startswith("stare scop"):
            goal = l.split(":")[1].strip()

    # Algoritm
    m = re.search(r"algoritmul\s+(BFS|DFS|UCS|GREEDY|ASTAR)", text, re.I)
    if m:
        algorithm = m.group(1).upper()

    return {
        "graph": graph,
        "start": start,
        "goal": goal,
        "algorithm": algorithm
    }

# ======================================================
# BFS
# ======================================================

def bfs(graph, start, goal):
    queue = deque([[start]])
    visited = {start}

    while queue:
        path = queue.popleft()
        node = path[-1]

        if node == goal:
            return path

        for neigh in graph.get(node, []):
            if neigh not in visited:
                visited.add(neigh)
                queue.append(path + [neigh])

    return None

# ======================================================
# DFS
# ======================================================

def dfs(graph, start, goal):
    stack = [(start, [start])]
    visited = set()

    while stack:
        node, path = stack.pop()

        if node == goal:
            return path

        if node in visited:
            continue

        visited.add(node)

        for neigh in reversed(graph.get(node, [])):
            stack.append((neigh, path + [neigh]))

    return None

# ======================================================
# UCS
# ======================================================

def ucs(graph, start, goal, costs):
    pq = [(0, start, [start])]
    visited = set()

    while pq:
        cost, node, path = heapq.heappop(pq)

        if node == goal:
            return path, cost

        if node in visited:
            continue

        visited.add(node)

        for neigh in graph.get(node, []):
            edge_cost = costs.get((node, neigh), 1)
            heapq.heappush(
                pq,
                (cost + edge_cost, neigh, path + [neigh])
            )

    return None, None

# ======================================================
# GREEDY BEST FIRST
# ======================================================

def greedy_best_first(graph, start, goal, heuristic):
    pq = [(heuristic.get(start, 0), start, [start])]
    visited = set()

    while pq:
        _, node, path = heapq.heappop(pq)

        if node == goal:
            return path

        if node in visited:
            continue

        visited.add(node)

        for neigh in graph.get(node, []):
            heapq.heappush(
                pq,
                (heuristic.get(neigh, 0), neigh, path + [neigh])
            )

    return None

# ======================================================
# A*
# ======================================================

def a_star(graph, start, goal, heuristic, costs):
    pq = [(heuristic.get(start, 0), 0, start, [start])]
    visited = set()

    while pq:
        f, g, node, path = heapq.heappop(pq)

        if node == goal:
            return path, g

        if node in visited:
            continue

        visited.add(node)

        for neigh in graph.get(node, []):
            edge_cost = costs.get((node, neigh), 1)
            g2 = g + edge_cost
            f2 = g2 + heuristic.get(neigh, 0)

            heapq.heappush(
                pq,
                (f2, g2, neigh, path + [neigh])
            )

    return None, None

# ======================================================
# SOLVER GENERAL
# ======================================================

def solve_search_problem(problem):
    graph = problem["graph"]
    start = problem["start"]
    goal = problem["goal"]
    alg = problem["algorithm"]

    if alg == "BFS":
        return bfs(graph, start, goal)

    if alg == "DFS":
        return dfs(graph, start, goal)

    if alg == "UCS":
        path, _ = ucs(graph, start, goal, problem.get("costs", {}))
        return path

    if alg == "GREEDY":
        return greedy_best_first(
            graph, start, goal,
            problem.get("heuristic", {})
        )

    if alg == "ASTAR":
        path, _ = a_star(
            graph, start, goal,
            problem.get("heuristic", {}),
            problem.get("costs", {})
        )
        return path

    return None

# ======================================================
# SCORARE RĂSPUNS
# ======================================================

def parse_user_path(text):
    if not text:
        return []

    return [
        x.strip()
        for x in re.split(r"->|→|,", text)
        if x.strip()
    ]

def compute_search_score(user_path, correct_path):
    if not user_path or not correct_path:
        return 0.0

    correct_prefix = 0
    for u, c in zip(user_path, correct_path):
        if u == c:
            correct_prefix += 1
        else:
            break

    prefix_score = correct_prefix / len(correct_path)
    goal_bonus = 0.2 if user_path[-1] == correct_path[-1] else 0.0

    return round(min(1.0, 0.8 * prefix_score + goal_bonus), 2)