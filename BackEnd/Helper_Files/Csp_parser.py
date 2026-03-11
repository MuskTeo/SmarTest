import re

def parse_csp_question_text(text):
    # -------- Variabile --------
    vars_match = re.search(r"Variabile:\s*(.+)", text)
    variables = [v.strip() for v in vars_match.group(1).split(",")]

    # -------- Domenii --------
    domains = {}
    domain_lines = re.findall(r"(\w+)\s*∈\s*\[([0-9,\s]+)\]", text)
    for var, values in domain_lines:
        domains[var] = [int(v) for v in values.split(",")]

    # -------- Constrângeri --------
    constraints = []
    constraint_lines = re.findall(r"(\w+)\s*(≠|<|<=|>)\s*(\w+)", text)

    for v1, op, v2 in constraint_lines:
        if op == "≠":
            cond = lambda a, b: a != b
        elif op == "<":
            cond = lambda a, b: a < b
        elif op == "<=":
            cond = lambda a, b: a <= b
        elif op == ">":
            cond = lambda a, b: a > b
        else:
            continue

        constraints.append((v1, v2, cond))

    # -------- Asignare parțială --------
    partial_assignment = {}
    partial_section = re.search(r"Asignare parțială:\s*(.+?)\n\n", text, re.S)

    if partial_section:
        assigns = re.findall(r"(\w+)\s*=\s*(\d+)", partial_section.group(1))
        for v, val in assigns:
            partial_assignment[v] = int(val)

    return variables, domains, constraints, partial_assignment
