from rest_framework import serializers

from .models import Achievement, Choice, GameSession, Scenario, SessionAchievement


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text', 'emoji_hint', 'choice_type']


class ScenarioSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Scenario
        fields = [
            'id',
            'title',
            'description',
            'context_detail',
            'location_emoji',
            'location_name',
            'witness_count',
            'inner_monologue',
            'choices',
        ]


class GameSessionSerializer(serializers.ModelSerializer):
    scenario = serializers.SerializerMethodField()

    class Meta:
        model = GameSession
        fields = ['session_id', 'confidence', 'awkwardness', 'scenario']

    def get_scenario(self, obj):
        if not obj.current_scenario:
            return None
        return ScenarioSerializer(obj.current_scenario).data


class AchievementSerializer(serializers.ModelSerializer):
    badge = serializers.CharField(source='badge_emoji')

    class Meta:
        model = Achievement
        fields = ['name', 'badge']


class SessionAchievementSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='achievement.name')
    badge = serializers.CharField(source='achievement.badge_emoji')

    class Meta:
        model = SessionAchievement
        fields = ['name', 'badge']
