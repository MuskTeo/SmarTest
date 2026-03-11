def score_variables(user_assign, variables):
    correct = len(set(user_assign.keys()) & set(variables))
    return correct / len(variables)


def score_domains(user_assign, domains):
    ok = 0
    for v, val in user_assign.items():
        if v in domains and val in domains[v]:
            ok += 1
    return ok / max(1, len(domains))


def score_constraints(user_assign, constraints):
    satisfied = 0
    total = 0

    for v1, v2, cond in constraints:
        if v1 in user_assign and v2 in user_assign:
            total += 1
            if cond(user_assign[v1], user_assign[v2]):
                satisfied += 1

    if total == 0:
        return 1.0  # nimic de verificat → ok
    return satisfied / total


def score_partial_assignment(user_assign, partial):
    if not partial:
        return 1.0
    ok = 0
    for v, val in partial.items():
        if user_assign.get(v) == val:
            ok += 1
    return ok / len(partial)

def compute_csp_partial_score(
    user_assign,
    variables,
    domains,
    constraints,
    partial
):
    s_vars = score_variables(user_assign, variables)
    s_dom = score_domains(user_assign, domains)
    s_con = score_constraints(user_assign, constraints)
    s_part = score_partial_assignment(user_assign, partial)

    final_score = (
        0.40 * s_vars +
        0.20 * s_dom +
        0.30 * s_con +
        0.10 * s_part
    )

    return round(final_score, 2)
