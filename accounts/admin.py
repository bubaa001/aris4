from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ProfileTrait, ArchiveTag, Quiz, Question, Choice, StudentQuizSubmission, AcademicClass, ClassContent

admin.site.register(User, UserAdmin)


@admin.register(AcademicClass)
class AcademicClassAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'instructor', 'schedule_string')
    list_filter = ('instructor',)
    search_fields = ('code', 'title')
    prepopulated_fields = {'slug': ('code',)}


@admin.register(ClassContent)
class ClassContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'academic_class', 'created_at')
    list_filter = ('academic_class',)


@admin.register(ProfileTrait)
class ProfileTraitAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ArchiveTag)
class ArchiveTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'academic_class', 'created_at')
    list_filter = ('creator', 'academic_class')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'order')
    list_filter = ('quiz',)
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct', 'order')


@admin.register(StudentQuizSubmission)
class StudentQuizSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'total', 'submitted_at')
