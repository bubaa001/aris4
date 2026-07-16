from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES=[
        ('student', 'student'),
        ('instructor', 'instructor'),
        ('admin', 'admin'),
        ('parent', 'parent'),
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
    meeting_link = models.CharField(max_length=200, blank=True, default='')
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


class Quiz(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'instructor'}, related_name='created_quizzes')
    academic_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    challenge = models.ForeignKey('Challenge', on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True, help_text='Link to a challenge event (for competition quizzes)')
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


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    avatar = models.ImageField(upload_to='student_avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True, help_text="Tell us about yourself")
    inspire_message = models.CharField(max_length=280, blank=True, null=True, help_text="A message to inspire others")
    favorite_quote = models.CharField(max_length=500, blank=True, null=True, help_text="Your favorite quote")
    parent_names = models.JSONField(default=list, blank=True, help_text="List of connected parent/guardian names")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Student Profile"

    def has_profile(self):
        return bool(self.avatar or self.bio or self.inspire_message or self.favorite_quote or self.parent_names)


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=500)
    link = models.CharField(max_length=300, blank=True, default='')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{'read' if self.is_read else 'new'}] {self.user.username}: {self.message[:60]}"


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


class ParentChildLink(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='parent_links')
    child = models.ForeignKey(User, on_delete=models.CASCADE, related_name='child_links')
    link_code = models.CharField(max_length=12, unique=True, blank=True)
    relationship_label = models.CharField(max_length=50, blank=True, default='')
    linked_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.link_code:
            import secrets
            import string
            alphabet = string.ascii_uppercase + string.digits
            self.link_code = 'PRNT-' + ''.join(secrets.choice(alphabet) for _ in range(6))
        super().save(*args, **kwargs)

    def __str__(self):
        child_name = self.child.username if self.child else '?'
        parent_name = self.parent.username if self.parent else 'UNLINKED'
        return f"{parent_name} \u2192 {child_name}"


class Challenge(models.Model):
    """Admin-hosted challenge/competition event."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    rules = models.TextField(blank=True, help_text='Challenge rules displayed to participants')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_superuser': True})
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    prize_pool_xp = models.IntegerField(default=0, help_text='Bonus XP awarded to winners')
    classes = models.ManyToManyField('AcademicClass', through='ChallengeClass', related_name='challenges')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def total_participants(self):
        return User.objects.filter(
            enrolled_classes__in=self.classes.all(), role='student'
        ).distinct().count()

    @property
    def status(self):
        from django.utils import timezone
        now = timezone.now()
        if now < self.start_date:
            return 'upcoming'
        elif now > self.end_date:
            return 'ended'
        return 'active'


class ChallengeClass(models.Model):
    """Links a class to a challenge."""
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='class_links')
    academic_class = models.ForeignKey('AcademicClass', on_delete=models.CASCADE, related_name='challenge_links')

    class Meta:
        unique_together = ['challenge', 'academic_class']

    def __str__(self):
        return f"{self.challenge.title} — {self.academic_class.code}"
