import random

def calculate_credit_score(data):
    """
    Temporary dummy scoring logic.
    Later replaced with ML model.
    """

    probability = random.uniform(0, 1)

    score = int(900 * (1 - probability))

    if probability < 0.3:
        risk = "Low"
    elif probability < 0.6:
        risk = "Medium"
    else:
        risk = "High"

    return score, risk, probability
