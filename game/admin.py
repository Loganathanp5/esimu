from django.contrib import admin

from .models import Achievement, Choice, GameSession, Scenario, SessionAchievement


class ChoiceInline(admin.TabularInline):
    model = Choice
    fk_name = 'scenario'
    extra = 0


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'order', 'witness_count')
    list_filter = ('category',)
    search_fields = ('title', 'description')
    inlines = [ChoiceInline]


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'confidence', 'awkwardness', 'is_completed', 'started_at')
    readonly_fields = ('session_id', 'started_at', 'completed_at')


admin.site.register(Achievement)
admin.site.register(SessionAchievement)
