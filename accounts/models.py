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


class AcademicClass(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    schedule_string = models.CharField(max_length=100)
    location_room = models.CharField(max_length=100)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='enrolled_classes', blank=True)
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'instructor'}, related_name='taught_classes')
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.title}"
    

class Module(models.Model):
    academic_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.academic_class.code} - {self.title}"


class ClassContent(models.Model):
    academic_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE, related_name='contents')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='contents', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='class_contents/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.academic_class.code} - {self.title}"


class ArchiveCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
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
    subtitle = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField()
    layout_variant = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='standard')
    status_label = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    timestamp_string = models.CharField(max_length=50)
    is_italic = models.BooleanField(default=False)
    
    has_certificate = models.BooleanField(default=False)
    certificate_url = models.URLField(blank=True, null=True)
    has_actions = models.BooleanField(default=False)
    download_url = models.URLField(blank=True, null=True)
    
    is_featured = models.BooleanField(default=False)
    cover_image = models.ImageField(upload_to='archive/covers/', blank=True, null=True)

    def __str__(self):
        return self.title    


class ProfileTrait(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class ArchiveTag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Quiz(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'instructor'}, related_name='created_quizzes')
    academic_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text


class LibraryBook(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to='library/books/')
    thumbnail = models.ImageField(upload_to='library/thumbnails/', blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'instructor'}, related_name='uploaded_books')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    academic_class = models.ForeignKey(AcademicClass, on_delete=models.SET_NULL, null=True, blank=True, related_name='library_books')

    def __str__(self):
        return self.title


class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    title_role = models.CharField(max_length=200, blank=True, null=True, help_text="e.g. Lead Instructor, Professor of Mathematics")
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='instructor_avatars/', blank=True, null=True)
    established_year = models.IntegerField(default=2024)
    
    # Academic focus areas (stored as JSON array of {title, description})
    academic_focus = models.JSONField(default=list, blank=True)
    
    # Core methodologies (stored as JSON array of {name})
    methodologies = models.JSONField(default=list, blank=True)
    
    # Published manuscripts (stored as JSON array of {publication_year, title, publisher_tag})
    manuscripts = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def has_profile(self):
        """Check if the instructor has filled out their profile."""
        return bool(self.bio or self.academic_focus or self.methodologies)


class StudentQuizSubmission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_submissions')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='submissions')
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    answers = models.JSONField(default=dict, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'quiz']

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} ({self.score}/{self.total})"
