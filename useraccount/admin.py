# useraccount/admin.py

from django.contrib import admin
from .models import UserProfile, Skill

from .models import (
    UserProfile,
    Skill,
    Quiz,
    Question
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_skills_to_teach_short', 'get_skills_to_learn_short', 'current_level']
    list_filter = ['current_level', 'student_status']
    search_fields = ['user__username', 'skills_to_teach', 'skills_to_learn']
    
    def get_skills_to_teach_short(self, obj):
        skills = obj.get_skills_to_teach_list()
        return ', '.join(skills[:3]) + ('...' if len(skills) > 3 else '')
    get_skills_to_teach_short.short_description = 'Teaches'
    
    def get_skills_to_learn_short(self, obj):
        skills = obj.get_skills_to_learn_list()
        return ', '.join(skills[:3]) + ('...' if len(skills) > 3 else '')
    get_skills_to_learn_short.short_description = 'Wants to learn'

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name']
    
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "quiz_type",
    ]
    
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "quiz",
        "question_text",
        "correct_answer",
    ]