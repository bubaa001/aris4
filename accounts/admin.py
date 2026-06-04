from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Quest, User

admin.site.register(User, UserAdmin)


# Register your models here.
@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'level', 'created_at')
    list_filter = ('level', 'creator')
    search_fields = ('title', 'description')