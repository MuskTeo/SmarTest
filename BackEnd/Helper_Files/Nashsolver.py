def solve_nash(strategies, payoff_dict):
    num_players = len(strategies)
    nash_points = []

    for combo, payoff in payoff_dict.items():
        ok = True
        for p in range(num_players):
            current_strategy = combo[p]
            current_payoff = payoff[p]

            for alt in range(len(strategies[p])):
                if alt == current_strategy:
                    continue
                new_combo = list(combo)
                new_combo[p] = alt
                new_combo = tuple(new_combo)

                if new_combo in payoff_dict:
                    if payoff_dict[new_combo][p] > current_payoff:
                        ok = False
                        break

            if not ok:
                break

        if ok:
            nash_points.append(combo)

    if not nash_points:
        return "Jocul NU are un echilibru Nash în strategii pure."

    return f"Acest joc ARE echilibru Nash în punctele: {nash_points}"