from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone


# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES=[
        ('student', 'student'),
        ('instructor', 'instructor'),
        ('admin', 'admin'),
        ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_approved = models.BooleanField(default=False)

    xp = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Quest(models.Model):
    LEVEL_CHOICES = [
        ('form_1', 'Form 1'),
        ('form_2', 'Form 2'),
        ('form_3', 'Form 3'),
        ('form_4', 'Form 4'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'instructor'}, related_name='created_quests')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='form_1')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_level_display()})"

class AcademicClass(models.Model):
    code = models.CharField(max_length=20, unique=True) # e.g., 'CS-402'
    title = models.CharField(max_length=200) # e.g., 'Advanced Visual Systems'
    schedule_string = models.CharField(max_length=100) # e.g., 'MONDAYS 14:00'
    location_room = models.CharField(max_length=100) # e.g., 'RM 402'
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='enrolled_classes', blank=True)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.title}"
    

class Deadline(models.Model):
    TYPE_CHOICES = [
        ('QUIZ', 'Quiz'),
        ('ESSAY', 'Essay'),
    ]
    academic_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE, related_name='deadlines')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='QUIZ')
    title = models.CharField(max_length=200)
    due_date = models.DateTimeField()
    cover_image = models.ImageField(upload_to='deadlines/covers/', blank=True, null=True)

    def __str__(self):
        return f"[{self.type}] {self.title} (Due: {self.due_date.strftime('%m.%d')})"
    
class ArchiveCategory(models.Model):
    name = models.CharField(max_length=100, unique=True) # e.g., 'Courses', 'Readings'
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name
    

class ArchiveItem(models.Model):
    LAYOUT_CHOICES = [
        ('standard', 'Standard Informational'),
        ('reading', 'Reading Container Block'),
        ('quote', 'Border Left Accent Callout'),
    ]
    STATUS_CHOICES = [
        ('COMPLETED', 'Completed'),
        ('ARCHIVED', 'Archived'),
    ]
    category = models.ForeignKey(ArchiveCategory, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True, null=True) # Used by 'reading' variant
    description = models.TextField()
    layout_variant = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='standard')
    status_label = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    timestamp_string = models.CharField(max_length=50) # e.g., 'Q3 2023' or 'SEP 14'
    is_italic = models.BooleanField(default=False)
    
    # Action tray logic
    has_certificate = models.BooleanField(default=False)
    certificate_url = models.URLField(blank=True, null=True)
    has_actions = models.BooleanField(default=False)
    download_url = models.URLField(blank=True, null=True)
    
    # Feature block flag
    is_featured = models.BooleanField(default=False)
    cover_image = models.ImageField(upload_to='archive/covers/', blank=True, null=True)

    def __str__(self):
        return self.title    
