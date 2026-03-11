import random

def generate_random_csp(num_vars=4,domain_size=3,num_constraints=4,max_partial_assignments=2):
    variables = [f"X{i}" for i in range(1, num_vars + 1)]

    domains = {
        var: list(range(1, domain_size + 1))
        for var in variables
    }

    possible_conditions = [
        lambda a, b: a != b,
        lambda a, b: a < b,
        lambda a, b: a <= b,
        lambda a, b: a > b
    ]

    constraints = []
    used_pairs = set()

    while len(constraints) < num_constraints:
        v1, v2 = random.sample(variables, 2)
        if (v1, v2) not in used_pairs:
            condition = random.choice(possible_conditions)
            constraints.append((v1, v2, condition))
            used_pairs.add((v1, v2))

    partial_assignment = {}
    for var in random.sample(variables, random.randint(0, max_partial_assignments)):
        partial_assignment[var] = random.choice(domains[var])

    return variables, domains, constraints, partial_assignment


def constraint_to_text(v1, v2, condition):
    if condition(1, 2) and not condition(2, 1):
        return f"{v1} < {v2}"
    if condition(1, 1) and not condition(1, 2):
        return f"{v1} = {v2}"
    if not condition(1, 1):
        return f"{v1} ≠ {v2}"
    return f"relație între {v1} și {v2}"

def generate_csp_question_text(variables, domains, constraints, partial_assignment):
    text = "Se consideră următoarea problemă CSP:\n\n"

    text += "Variabile:\n"
    text += ", ".join(variables) + "\n\n"

    text += "Domenii:\n"
    for var in variables:
        text += f"  {var} ∈ {domains[var]}\n"

    text += "\nConstrângeri:\n"
    for v1, v2, cond in constraints:
        text += f"  {constraint_to_text(v1, v2, cond)}\n"

    if partial_assignment:
        text += "\nAsignare parțială:\n"
        for var, val in partial_assignment.items():
            text += f"  {var} = {val}\n"
    else:
        text += "\nAsignare parțială: ∅\n"

    text += (
        "\nCerință:\n"
        "Continuați rezolvarea folosind algoritmul Backtracking cu Forward Checking "
        "și determinați o asignare completă, dacă există.\n"
    )

    return text
