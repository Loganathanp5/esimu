import uuid

from django.db import models


class Scenario(models.Model):
    CATEGORY_CHOICES = [
        ('campus', 'Campus Catastrophes'),
        ('food', 'Food Court Fiascos'),
        ('social', 'Social Misfires'),
        ('digital', 'Digital Disasters'),
        ('public', 'Public Nightmares'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    context_detail = models.CharField(max_length=300)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    location_emoji = models.CharField(max_length=10, default='LOC')
    location_name = models.CharField(max_length=100)
    witness_count = models.IntegerField(default=0)
    is_start = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    inner_monologue = models.TextField(blank=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title


class Choice(models.Model):
    CHOICE_TYPE_CHOICES = [
        ('ignore', 'Pretend Nothing Happened'),
        ('laugh', 'Laugh It Off'),
        ('escape', 'Escape The Situation'),
        ('escalate', 'Make It Worse'),
    ]

    scenario = models.ForeignKey(
        Scenario,
        related_name='choices',
        on_delete=models.CASCADE,
    )
    text = models.CharField(max_length=200)
    choice_type = models.CharField(max_length=20, choices=CHOICE_TYPE_CHOICES)
    emoji_hint = models.CharField(max_length=10, default='>')
    confidence_effect = models.IntegerField()
    awkwardness_effect = models.IntegerField()
    outcome_text = models.TextField()
    witness_reaction = models.CharField(max_length=200, blank=True)
    next_scenario = models.ForeignKey(
        Scenario,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='previous_choices',
    )
    triggers_callback = models.BooleanField(default=False)
    callback_text = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return f'{self.scenario.title}: {self.text[:35]}'


class GameSession(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    confidence = models.IntegerField(default=50)
    awkwardness = models.IntegerField(default=0)
    current_scenario = models.ForeignKey(
        Scenario,
        null=True,
        on_delete=models.SET_NULL,
    )
    scenario_pool = models.JSONField(default=list)
    current_index = models.IntegerField(default=0)
    choices_made = models.JSONField(default=list)
    is_completed = models.BooleanField(default=False)
    final_score = models.IntegerField(null=True, blank=True)
    ending_title = models.CharField(max_length=100, blank=True)
    ending_description = models.CharField(max_length=240, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.IntegerField(null=True, blank=True)
    timer_mode = models.BooleanField(default=False)
    random_mode = models.BooleanField(default=True)

    def __str__(self):
        return f'Session {self.session_id}'


class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=300)
    badge_emoji = models.CharField(max_length=10)
    condition_type = models.CharField(max_length=50)
    condition_value = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class SessionAchievement(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session', 'achievement')

    def __str__(self):
        return f'{self.session.session_id} - {self.achievement.name}'
