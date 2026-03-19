import random
from datetime import timedelta

from django.db import DatabaseError
from django.db import transaction
from django.utils import timezone

from .models import Achievement, Choice, GameSession, Scenario, SessionAchievement

ENDING_TABLE = [
    (80, 'Smooth Operator', 'You turned every awkward moment into a flex. Are you even human?'),
    (60, 'Social Chameleon', 'You adapted and survived with minimal damage.'),
    (40, 'Social Survivor', 'You made it through, but your dignity took some hits.'),
    (20, 'Walking Cringe', 'Every room you enter now remembers something.'),
    (-999, 'Embarrassment Legend', 'Maximum cringe achieved. Science needs your data.'),
]


def embarrassment_level(confidence: int, awkwardness: int) -> int:
    return awkwardness + (100 - confidence)


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def get_scenario_pool(random_mode: bool, total: int = 10):
    try:
        scenario_ids = list(Scenario.objects.values_list('id', flat=True))
    except DatabaseError as exc:
        raise ValueError(
            'Database is not ready. Run migrations and seed data (python manage.py migrate && python manage.py seed_data).'
        ) from exc
    if random_mode:
        random.shuffle(scenario_ids)
    return scenario_ids[:total]


def _serialize_progress(session: GameSession):
    return {
        'current': min(session.current_index + 1, len(session.scenario_pool)),
        'total': len(session.scenario_pool),
    }


def start_game(timer_mode: bool = False, random_mode: bool = True) -> GameSession:
    pool = get_scenario_pool(random_mode=random_mode)
    if not pool:
        raise ValueError('No scenarios found. Run seed command first.')

    first_scenario = Scenario.objects.get(id=pool[0])
    session = GameSession.objects.create(
        current_scenario=first_scenario,
        scenario_pool=pool,
        timer_mode=timer_mode,
        random_mode=random_mode,
    )
    return session


@transaction.atomic
def apply_choice(session: GameSession, choice: Choice):
    if session.is_completed:
        raise ValueError('This session is already completed.')
    if session.current_scenario_id != choice.scenario_id:
        raise ValueError('Choice does not belong to current scenario.')

    old_confidence = session.confidence
    old_awkwardness = session.awkwardness

    session.confidence = clamp(session.confidence + choice.confidence_effect, 0, 100)
    session.awkwardness = clamp(session.awkwardness + max(0, choice.awkwardness_effect), 0, 100)

    callback_triggered = None
    if choice.triggers_callback and choice.callback_text:
        callback_triggered = choice.callback_text

    session.choices_made.append(
        {
            'scenario_id': choice.scenario_id,
            'scenario_title': choice.scenario.title,
            'choice_id': choice.id,
            'choice_text': choice.text,
            'choice_type': choice.choice_type,
            'confidence_effect': choice.confidence_effect,
            'awkwardness_effect': choice.awkwardness_effect,
            'witness_count': choice.scenario.witness_count,
            'outcome_text': choice.outcome_text,
            'timestamp': timezone.now().isoformat(),
        }
    )

    session.current_index += 1
    next_scenario = _next_scenario(session, choice)

    if next_scenario is None:
        finalize_session(session)
    else:
        session.current_scenario = next_scenario

    session.save()

    return {
        'outcome_text': choice.outcome_text,
        'inner_monologue': choice.scenario.inner_monologue,
        'witness_reaction': choice.witness_reaction or default_witness_text(choice.scenario.witness_count),
        'score_changes': {
            'confidence': session.confidence - old_confidence,
            'awkwardness': session.awkwardness - old_awkwardness,
        },
        'updated_scores': {
            'confidence': session.confidence,
            'awkwardness': session.awkwardness,
            'embarrassment_level': embarrassment_level(session.confidence, session.awkwardness),
        },
        'callback_triggered': callback_triggered,
        'next_scenario': session.current_scenario,
        'progress': _serialize_progress(session),
        'is_completed': session.is_completed,
    }


def _next_scenario(session: GameSession, choice: Choice):
    if choice.next_scenario_id:
        return choice.next_scenario

    if session.current_index >= len(session.scenario_pool):
        return None
    next_id = session.scenario_pool[session.current_index]
    return Scenario.objects.get(id=next_id)


def default_witness_text(witness_count: int):
    if witness_count == 0:
        return 'No one noticed. A rare social miracle.'
    return f'{witness_count} people definitely noticed that.'


def finalize_session(session: GameSession):
    if session.is_completed:
        return

    bonus = calculate_bonus(session)
    score = session.confidence - session.awkwardness + bonus
    title, description = classify_ending(score)

    session.is_completed = True
    session.final_score = score
    session.ending_title = title
    session.ending_description = description
    session.completed_at = timezone.now()
    session.time_taken_seconds = int((session.completed_at - session.started_at).total_seconds())


def classify_ending(score: int):
    for minimum, title, description in ENDING_TABLE:
        if score >= minimum:
            return title, description
    return ENDING_TABLE[-1][1], ENDING_TABLE[-1][2]


def calculate_bonus(session: GameSession) -> int:
    choices = session.choices_made
    if not choices:
        return 0

    bonus = 0
    choice_types = {entry['choice_type'] for entry in choices}
    if len(choice_types) == 1:
        bonus += 5

    if session.timer_mode and session.time_taken_seconds and session.time_taken_seconds < 180:
        bonus += 3

    callback_count = sum(1 for c in choices if c.get('choice_type') == 'escalate')
    if callback_count >= 3:
        bonus += 7

    return bonus


def format_duration(seconds: int | None) -> str:
    if seconds is None:
        return '0m 00s'
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    minutes, rem = divmod(total_seconds, 60)
    return f'{minutes}m {rem:02d}s'


def unlock_achievements(session: GameSession):
    unlocked = []
    achievements = Achievement.objects.all()
    made = session.choices_made

    for achievement in achievements:
        if meets_condition(achievement, session, made):
            obj, created = SessionAchievement.objects.get_or_create(
                session=session,
                achievement=achievement,
            )
            if created:
                unlocked.append(obj)

    return unlocked


def meets_condition(achievement: Achievement, session: GameSession, made: list[dict]) -> bool:
    ctype = achievement.condition_type
    threshold = achievement.condition_value

    if ctype == 'max_awkward':
        return session.awkwardness >= threshold
    if ctype == 'max_confidence':
        return session.confidence >= threshold
    if ctype == 'speed' and session.time_taken_seconds is not None:
        return session.time_taken_seconds <= threshold
    if ctype in ('all_escalate', 'all_nuclear'):
        return bool(made) and all(choice['choice_type'] == 'escalate' for choice in made)
    if ctype in ('no_escalate', 'no_bold'):
        return bool(made) and all(choice['choice_type'] != 'escalate' for choice in made)
    return False


def result_payload(session: GameSession):
    if not session.is_completed:
        finalize_session(session)
        session.save()

    unlock_achievements(session)

    achievements = SessionAchievement.objects.select_related('achievement').filter(session=session)
    worst = max(session.choices_made, key=lambda x: x.get('awkwardness_effect', 0), default=None)
    total_witnesses = sum(item.get('witness_count', 0) for item in session.choices_made)

    return {
        'final_score': session.final_score,
        'ending_title': session.ending_title,
        'ending_description': session.ending_description,
        'stats': {
            'confidence_final': session.confidence,
            'awkwardness_final': session.awkwardness,
            'scenarios_completed': len(session.choices_made),
            'time_taken': format_duration(session.time_taken_seconds),
            'worst_moment': worst.get('choice_text') if worst else '',
            'witnesses_traumatized': total_witnesses,
        },
        'achievements': [
            {
                'name': item.achievement.name,
                'badge': item.achievement.badge_emoji,
            }
            for item in achievements
        ],
        'share_card': {
            'title': f'I scored {session.final_score} on Embarrassment Simulator',
            'subtitle': session.ending_title,
            'url': f'/result/{session.session_id}/',
        },
    }
