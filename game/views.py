import uuid

from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Choice, GameSession
from .serializers import ScenarioSerializer
from .services import apply_choice, result_payload, start_game


@require_GET
def index(request):
    return render(request, 'game/index.html')


@require_GET
def game_page(request):
    return render(request, 'game/game.html')


@require_GET
def result_page(request, session_id):
    return render(request, 'game/result.html', {'session_id': session_id})


@api_view(['POST'])
def api_start(request):
    timer_mode = bool(request.data.get('timer_mode', False))
    random_mode = bool(request.data.get('random_mode', True))

    try:
        session = start_game(timer_mode=timer_mode, random_mode=random_mode)
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            'session_id': str(session.session_id),
            'confidence': session.confidence,
            'awkwardness': session.awkwardness,
            'scenario': ScenarioSerializer(session.current_scenario).data,
            'progress': {'current': 1, 'total': len(session.scenario_pool)},
            'timer_mode': session.timer_mode,
            'random_mode': session.random_mode,
        }
    )


@api_view(['POST'])
def api_choose(request):
    session_id = request.data.get('session_id')
    choice_id = request.data.get('choice_id')

    if not session_id or not choice_id:
        return Response({'detail': 'session_id and choice_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        session_uuid = uuid.UUID(str(session_id))
    except ValueError:
        return Response({'detail': 'Invalid session_id format.'}, status=status.HTTP_400_BAD_REQUEST)

    session = get_object_or_404(GameSession, session_id=session_uuid)
    choice = get_object_or_404(Choice, id=choice_id)

    try:
        payload = apply_choice(session, choice)
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    next_scenario = payload.pop('next_scenario')
    payload['next_scenario'] = ScenarioSerializer(next_scenario).data if next_scenario else None
    if payload['is_completed']:
        payload['result_url'] = f'/result/{session.session_id}/'
    return Response(payload)


@api_view(['GET'])
def api_result(request, session_id):
    try:
        session_uuid = uuid.UUID(str(session_id))
    except ValueError:
        return Response({'detail': 'Invalid session_id format.'}, status=status.HTTP_400_BAD_REQUEST)

    session = get_object_or_404(GameSession, session_id=session_uuid)
    payload = result_payload(session)
    session.save()
    return Response(payload)
