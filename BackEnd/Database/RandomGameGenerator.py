import itertools
import random

def generate_random_game(num_players, min_str=2, max_str=3, payoff_min=0, payoff_max=10):
    strategies = [
        list(range(random.randint(min_str, max_str)))
        for _ in range(num_players)
    ]

    game = {}
    for combo in itertools.product(*strategies):
        payoff = [random.randint(payoff_min, payoff_max) for _ in range(num_players)]
        game[combo] = payoff

    
    pay_json = {str(k): v for k, v in game.items()}

    return strategies, pay_json

def hardcoded_games():
    games = []

    
    strategies = [[0,1], [0,1]]
    payoffs = {
        "(0,0)": [2,2],
        "(0,1)": [0,1],
        "(1,0)": [1,0],
        "(1,1)": [0,0],
    }
    games.append((strategies, payoffs))

   
    strategies = [[0,1], [0,1]]
    payoffs = {
        "(0,0)": [1,1],
        "(0,1)": [0,2],
        "(1,0)": [2,0],
        "(1,1)": [3,3],
    }
    games.append((strategies, payoffs))

   
    strategies = [[0,1], [0,1]]
    payoffs = {
        "(0,0)": [-1,-1],
        "(0,1)": [-3,0],
        "(1,0)": [0,-3],
        "(1,1)": [-2,-2],
    }
    games.append((strategies, payoffs))

    
    strategies = [[0,1,2], [0,1,2]]
    payoffs = {
        "(0,0)": [5,5],
        "(0,1)": [0,1],
        "(0,2)": [1,0],
        "(1,0)": [1,0],
        "(1,1)": [0,0],
        "(1,2)": [0,1],
        "(2,0)": [0,1],
        "(2,1)": [1,0],
        "(2,2)": [0,0],
    }
    games.append((strategies, payoffs))

    
    strategies = [[0,1], [0,1]]
    payoffs = {
        "(0,0)": [3,3],
        "(0,1)": [0,0],
        "(1,0)": [0,0],
        "(1,1)": [2,2],
    }
    games.append((strategies, payoffs))

    return games
