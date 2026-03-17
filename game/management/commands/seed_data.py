from django.core.management.base import BaseCommand

from game.models import Achievement, Choice, Scenario

OPTION_TYPES = ['ignore', 'laugh', 'escape', 'escalate']

OPTION_EFFECTS = {
    'ignore': {'confidence_effect': -2, 'awkwardness_effect': 3, 'emoji_hint': ':|'},
    'laugh': {'confidence_effect': 2, 'awkwardness_effect': 1, 'emoji_hint': ':)'},
    'escape': {'confidence_effect': -5, 'awkwardness_effect': 2, 'emoji_hint': '>>'},
    'escalate': {'confidence_effect': -8, 'awkwardness_effect': 8, 'emoji_hint': '!!'},
}

OPTION_TEXT_VARIATIONS = {
    'ignore': [
        'Pretend nothing happened.',
        'Act normal and ignore it.',
        'Look away casually and continue.',
        'Play it off like that was intentional.',
    ],
    'laugh': [
        'Laugh it off and acknowledge the moment.',
        'Give a nervous laugh and keep talking.',
        'Smile and make a small joke about it.',
        'Try to cover it with a quick laugh.',
    ],
    'escape': [
        'Walk away quickly and avoid eye contact.',
        'Check your phone and leave the scene.',
        'Exit immediately before things get worse.',
        'Disappear from existence for a minute.',
    ],
    'escalate': [
        'Double down and make it worse.',
        'Overreact dramatically in public.',
        'Commit harder and escalate the chaos.',
        'Do it again with full confidence.',
    ],
}

OPTION_OUTCOMES = {
    'ignore': 'You acted normal, but people still noticed.',
    'laugh': 'Some people laughed with you. A few still cringed.',
    'escape': 'You escaped the scene, but your confidence took a hit.',
    'escalate': 'You escalated everything. The story will be retold for weeks.',
}

OPTION_WITNESS_REACTIONS = {
    'ignore': 'People exchanged looks but let it slide.',
    'laugh': 'The room softened for a second, then moved on.',
    'escape': 'Everyone watched you leave at high speed.',
    'escalate': 'Witnesses are now emotionally invested in your downfall.',
}

SCENARIOS = [
    {
        'title': 'Wrong Classroom Entry',
        'description': 'You walked into the wrong class and sat down. The professor stares at you while everyone else knows each other.',
        'context_detail': '12 students are watching this unfold.',
        'category': 'campus',
        'location_name': 'Lecture Hall B2',
        'location_emoji': 'SCH',
        'witness_count': 12,
        'inner_monologue': 'Play it cool. This is definitely not your class.',
    },
    {
        'title': 'Confidently Wrong Answer',
        'description': 'You raise your hand and answer with full confidence. The room goes silent for three seconds.',
        'context_detail': 'The professor is still looking at you.',
        'category': 'campus',
        'location_name': 'Seminar Room',
        'location_emoji': 'SCH',
        'witness_count': 21,
        'inner_monologue': 'Why did I use that tone? Why so confident?',
    },
    {
        'title': 'Called Professor Mom',
        'description': 'You asked a question and accidentally said "Mom" instead of "Professor." Someone in back just opened camera mode.',
        'context_detail': 'Everyone heard it clearly.',
        'category': 'campus',
        'location_name': 'Main Auditorium',
        'location_emoji': 'SCH',
        'witness_count': 35,
        'inner_monologue': 'Delete this memory from every brain right now.',
    },
    {
        'title': 'You Too at Lunch',
        'description': 'Waiter says, "Enjoy your meal." You reply, "You too." They heard it. They did not react.',
        'context_detail': 'People at nearby tables definitely heard.',
        'category': 'food',
        'location_name': 'Campus Cafe',
        'location_emoji': 'FOD',
        'witness_count': 17,
        'inner_monologue': 'I should not be allowed in public.',
    },
    {
        'title': 'Door Logic Failure',
        'description': 'You pull a push door, then push a pull door, then repeat both. A line forms behind you.',
        'context_detail': '8 people are waiting and learning patience.',
        'category': 'food',
        'location_name': 'Food Court Exit',
        'location_emoji': 'FOD',
        'witness_count': 8,
        'inner_monologue': 'This is not a door. This is a social puzzle.',
    },
    {
        'title': 'Wrong Wave in Restaurant',
        'description': 'You wave at someone you think you know. It is not them. Their actual friend walks past you.',
        'context_detail': 'Nearby tables are now invested.',
        'category': 'food',
        'location_name': 'Downtown Diner',
        'location_emoji': 'FOD',
        'witness_count': 14,
        'inner_monologue': 'Maybe I can become invisible for ten minutes.',
    },
    {
        'title': 'Handshake Fist-Bump Collision',
        'description': 'You go for handshake. They go for fist-bump. You hold their fist anyway.',
        'context_detail': 'Your crush is standing two feet away.',
        'category': 'social',
        'location_name': 'Student Club Booth',
        'location_emoji': 'SOC',
        'witness_count': 9,
        'inner_monologue': 'What shape is social contact supposed to be?',
    },
    {
        'title': 'Wrong Laugh at Meeting',
        'description': 'Someone talks about budget cuts. You laugh because you thought it was a joke.',
        'context_detail': 'Your boss has paused the meeting.',
        'category': 'social',
        'location_name': 'Team Room 4',
        'location_emoji': 'SOC',
        'witness_count': 11,
        'inner_monologue': 'Rewind. Rewind. Rewind.',
    },
    {
        'title': 'Baby Shark in Library',
        'description': 'Your phone blasts music at full volume in a silent library. The song is Baby Shark.',
        'context_detail': 'A librarian is already walking toward you.',
        'category': 'social',
        'location_name': 'University Library',
        'location_emoji': 'SOC',
        'witness_count': 23,
        'inner_monologue': 'This is how legends are born and banned.',
    },
    {
        'title': 'Liked a 3-Year-Old Photo',
        'description': 'You are deep in someone profile and accidentally liked an old photo. They are online right now.',
        'context_detail': 'Seen at 2:13 PM.',
        'category': 'digital',
        'location_name': 'Phone Screen',
        'location_emoji': 'DIG',
        'witness_count': 1,
        'inner_monologue': 'The app should have an undo for this exact crisis.',
    },
    {
        'title': 'Complaint Sent to Target',
        'description': 'You typed a complaint message about someone and sent it directly to them.',
        'context_detail': 'They are typing a reply.',
        'category': 'digital',
        'location_name': 'Messaging App',
        'location_emoji': 'DIG',
        'witness_count': 1,
        'inner_monologue': 'Airplane mode can not save my reputation.',
    },
    {
        'title': 'Muted Presentation',
        'description': 'You presented for ten minutes while muted. Everyone waited politely.',
        'context_detail': 'You were using your serious presenter voice.',
        'category': 'digital',
        'location_name': 'Video Call',
        'location_emoji': 'DIG',
        'witness_count': 16,
        'inner_monologue': 'That was my best performance. For no one.',
    },
    {
        'title': 'Trip on Flat Ground',
        'description': 'You tripped in a crowded street where there was absolutely nothing to trip on.',
        'context_detail': 'A car honked in sympathy.',
        'category': 'public',
        'location_name': 'Main Street',
        'location_emoji': 'PUB',
        'witness_count': 27,
        'inner_monologue': 'Gravity has a personal issue with me.',
    },
    {
        'title': 'Wrong Direction U-Turn',
        'description': 'You walked the wrong way, realized it, and had to pass the same people again.',
        'context_detail': 'You pretend your phone gave new instructions.',
        'category': 'public',
        'location_name': 'Metro Walkway',
        'location_emoji': 'PUB',
        'witness_count': 19,
        'inner_monologue': 'Act natural. You are not acting natural.',
    },
    {
        'title': 'Too-Early Door Hold',
        'description': 'You held the door for someone too far away. They start jogging. You can not stop now.',
        'context_detail': 'Both of you are committed to the bit.',
        'category': 'public',
        'location_name': 'Office Entrance',
        'location_emoji': 'PUB',
        'witness_count': 10,
        'inner_monologue': 'This is now a trust exercise.',
    },
]

ACHIEVEMENTS = [
    {
        'name': 'Awkward King',
        'description': 'Reach very high awkwardness.',
        'badge_emoji': 'CROWN',
        'condition_type': 'max_awkward',
        'condition_value': 90,
    },
    {
        'name': 'Smooth Brain',
        'description': 'End with high confidence.',
        'badge_emoji': 'BRAIN',
        'condition_type': 'max_confidence',
        'condition_value': 85,
    },
    {
        'name': 'Speed Demon',
        'description': 'Finish quickly in timer mode.',
        'badge_emoji': 'FAST',
        'condition_type': 'speed',
        'condition_value': 120,
    },
    {
        'name': 'Chaos Agent',
        'description': 'Choose "Make It Worse" every time.',
        'badge_emoji': 'FIRE',
        'condition_type': 'all_escalate',
        'condition_value': 1,
    },
    {
        'name': 'Silent Sufferer',
        'description': 'Never choose "Make It Worse".',
        'badge_emoji': 'QUIET',
        'condition_type': 'no_escalate',
        'condition_value': 1,
    },
]


def build_option_payload(scenario_title: str, option_type: str, scenario_index: int) -> dict:
    effects = OPTION_EFFECTS[option_type]
    variations = OPTION_TEXT_VARIATIONS[option_type]
    variation = variations[scenario_index % len(variations)]

    return {
        'choice_type': option_type,
        'emoji_hint': effects['emoji_hint'],
        'text': variation,
        'confidence_effect': effects['confidence_effect'],
        'awkwardness_effect': effects['awkwardness_effect'],
        'outcome_text': f"{OPTION_OUTCOMES[option_type]} ({scenario_title})",
        'witness_reaction': OPTION_WITNESS_REACTIONS[option_type],
    }


class Command(BaseCommand):
    help = 'Seed embarrassment scenarios, choices, and achievements.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete existing scenarios before seeding.')

    def handle(self, *args, **options):
        if options['reset']:
            Choice.objects.all().delete()
            Scenario.objects.all().delete()

        created_scenarios = 0
        for idx, payload in enumerate(SCENARIOS, start=1):
            scenario, created = Scenario.objects.get_or_create(
                title=payload['title'],
                defaults={
                    **payload,
                    'order': idx,
                    'is_start': idx == 1,
                },
            )
            if created:
                created_scenarios += 1

            for option_type in OPTION_TYPES:
                defaults = build_option_payload(scenario.title, option_type, idx)
                choice, _ = Choice.objects.get_or_create(
                    scenario=scenario,
                    choice_type=option_type,
                    defaults=defaults,
                )
                for field, value in defaults.items():
                    setattr(choice, field, value)
                if scenario.category in ('digital', 'social') and option_type == 'escalate':
                    choice.triggers_callback = True
                    choice.callback_text = 'Someone remembers your earlier awkward moment and brings it up.'
                else:
                    choice.triggers_callback = False
                    choice.callback_text = ''
                choice.save()

        created_achievements = 0
        for payload in ACHIEVEMENTS:
            _, created = Achievement.objects.update_or_create(
                name=payload['name'],
                defaults=payload,
            )
            if created:
                created_achievements += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed complete. New scenarios: {created_scenarios}, new achievements: {created_achievements}.'
            )
        )
