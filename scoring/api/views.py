from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..services.scoring_engine import calculate_credit_score


@api_view(['POST'])
def score_application(request):

    data = request.data

    score, risk, prob = calculate_credit_score(data)

    return Response({
        "credit_score": score,
        "risk": risk,
        "probability_default": prob
    })
