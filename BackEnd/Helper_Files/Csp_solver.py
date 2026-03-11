from Csp_parser import parse_csp_question_text
from Restrictions import solve_csp_fc, format_solution

def get_csp_answer_from_text(question_text):
    variables, domains, constraints, partial_assignment = \
        parse_csp_question_text(question_text)

    solution = solve_csp_fc(
        variables,
        domains,
        constraints,
        partial_assignment
    )

    return format_solution(solution)
