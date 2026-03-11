def is_consistent(var, value, assignment, constraints):
    for (v1, v2, condition) in constraints:
        if var == v1 and v2 in assignment:
            if not condition(value, assignment[v2]):
                return False
        if var == v2 and v1 in assignment:
            if not condition(assignment[v1], value):
                return False
    return True

def forward_checking(var, value, domains, assignment, constraints):
    removed = {}

    for (v1, v2, condition) in constraints:
        if var == v1 and v2 not in assignment:
            removed[v2] = []
            for val in domains[v2]:
                if not condition(value, val):
                    removed[v2].append(val)
            domains[v2] = [v for v in domains[v2] if v not in removed[v2]]

            if not domains[v2]:
                return None

        if var == v2 and v1 not in assignment:
            removed[v1] = []
            for val in domains[v1]:
                if not condition(val, value):
                    removed[v1].append(val)
            domains[v1] = [v for v in domains[v1] if v not in removed[v1]]

            if not domains[v1]:
                return None

    return removed

def restore_domains(domains, removed):
    for var in removed:
        domains[var].extend(removed[var])

def select_unassigned_variable(variables, assignment):
    for var in variables:
        if var not in assignment:
            return var
    return None


def backtracking_fc(variables, domains, constraints, assignment):
    if len(assignment) == len(variables):
        return assignment

    var = select_unassigned_variable(variables, assignment)

    for value in domains[var][:]:
        if is_consistent(var, value, assignment, constraints):
            assignment[var] = value

            removed = forward_checking(var, value, domains, assignment, constraints)
            if removed is not None:
                result = backtracking_fc(variables, domains, constraints, assignment)
                if result is not None:
                    return result
                restore_domains(domains, removed)

            del assignment[var]

    return None


def solve_csp_fc(variables, domains, constraints, partial_assignment):
    assignment = partial_assignment.copy()
    domains = {v: domains[v][:] for v in domains}
    return backtracking_fc(variables, domains, constraints, assignment)

def format_solution(solution):
    if solution is None:
        return "Nu există nicio asignare completă care să satisfacă toate constrângerile."

    lines = ["Soluția CSP este:"]
    for var in sorted(solution.keys()):
        lines.append(f"  {var} = {solution[var]}")

    return "\n".join(lines)
