from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from types import SimpleNamespace
from .forms import RegisterForm, LoginForm
from .models import User, Quest, AcademicClass, Deadline, ArchiveCategory, ArchiveItem






def home_view(request):
    student_count = User.objects.filter(role='student').count()
    instructor_count = User.objects.filter(role='instructor').count()
    active_quests = Quest.objects.count()
   
    top_student = User.objects.filter(role='student').order_by('-xp').first()
    top_student_name = "NO SCHOLARS YET"
    top_student_xp = 0
    current_quest_title = "System Standby"
    active_title = "Initiate"
    if top_student:
        top_student_name = top_student.username.upper()
        top_student_xp = top_student.xp

        latest_quest = Quest.objects.filter(level='form_1').order_by('-created_at').first() # Can adapt level dynamically
        if latest_quest:
            current_quest_title = latest_quest.title
        elif Quest.objects.exists():
            current_quest_title = Quest.objects.latest('created_at').title

        if top_student_xp >= 2000:
            active_title = "Grandmaster"
        elif top_student_xp >= 1000:
            active_title = "Elite Scholar"
        else:
            active_title = "Alpha Vanguard"    
   
    context = {
        'student_count': student_count,
        'instructor_count': instructor_count,
        'active_quests_count': active_quests,
        'top_student_name': top_student_name,
        'top_student_xp': top_student_xp,
        'current_quest_title': current_quest_title,
        'active_title': active_title,
    }
    return render(request, 'home.html', context)

def tail(request):
    return render(request, 'test.html')


@ensure_csrf_cookie
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.role == 'student':
                return redirect('select_level')
            elif user.role == 'instructor':
                return redirect('pending_approval')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

@ensure_csrf_cookie
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.role == 'student':
                return redirect('study_dashboard')
            elif user.role == 'instructor':
                if user.is_approved:
                    return redirect('instructor_dashboard')
                return redirect('pending_approval')
            elif user.role == 'admin' or user.is_superuser:
                return redirect('admin_dashboard')
    else:
        form = LoginForm(request)
    return render(request, 'login.html', {'form': form})

def select_level_view(request):
    return render(request, 'select_level.html')

def instructor_dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.role != 'instructor':
        return redirect('home')
    if not request.user.is_approved:
        return redirect('pending_approval')
    return render(request, 'instructor_dashboard.html')


def pending_approval_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.role != 'instructor':
        return redirect('home')
    if request.user.is_approved:
        return redirect('instructor_dashboard')
    return render(request, 'pending_approval.html')


@login_required
def admin_dashboard_view(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden('Not authorized')

    pending_instructors = User.objects.filter(role='instructor', is_approved=False)
    approved_instructors = User.objects.filter(role='instructor', is_approved=True)

    return render(request, 'admin_approval.html', {
        'pending_instructors': pending_instructors,
        'approved_instructors': approved_instructors,
    })


@login_required
def approve_instructor_view(request, user_id):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden('Not authorized')
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    instructor = get_object_or_404(User, pk=user_id, role='instructor')
    instructor.is_approved = True
    instructor.save(update_fields=['is_approved'])
    return JsonResponse({'status': 'approved'})


@login_required
def disapprove_instructor_view(request, user_id):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden('Not authorized')
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    instructor = get_object_or_404(User, pk=user_id, role='instructor')
    instructor.is_approved = False
    instructor.save(update_fields=['is_approved'])
    return JsonResponse({'status': 'disapproved'})


def kamati_view(request, id):
    return render(request, 'kamati.html', {'kamati_id': id})


@login_required
def student_dashboard_view(request):
    user = request.user
    
    # Dynamic XP Tier System calculations for Level 14 Professional
    current_xp = user.xp if hasattr(user, 'xp') else 1250 # fallback for baseline standard models
    base_level = 14
    level_range_max = 2000
    level_range_min = 1000
    
    # Progress Math
    total_in_tier = level_range_max - level_range_min
    progress_in_tier = current_xp - level_range_min
    xp_percentage = int((progress_in_tier / total_in_tier) * 100) if total_in_tier > 0 else 100
    xp_to_next = max(0, level_range_max - current_xp)
    
    academic_status = {
        'semester_label': 'Spring Semester',
        'current_week': '08',
        'current_level': base_level,
        'tier_title': 'Professional' if current_xp >= 1000 else 'Initiate',
        'xp_percentage': min(100, max(0, xp_percentage)),
        'xp_to_next': xp_to_next,
    }
    
    # Query datasets
    active_deadlines = Deadline.objects.filter(due_date__gte=timezone.now()).order_by('due_date')[:2]
    enrolled_classes = AcademicClass.objects.filter(students=user)
    
    context = {
        'current_student': user,
        'academic_status': academic_status,
        'active_deadlines': active_deadlines,
        'enrolled_classes': enrolled_classes,
    }
    return render(request, 'student_dashboard.html', context)


def archive_index_view(request):
    categories = ArchiveCategory.objects.all()
    archive_items = ArchiveItem.objects.all().order_by('-id')
    featured_record = ArchiveItem.objects.filter(is_featured=True).first()
    
    context = {
        'categories': categories,
        'archive_items': archive_items,
        'featured_record': featured_record,
        'active_category': None, # Means 'ALL_RECORDS' is selected
    }
    return render(request, 'archive_repository.html', context)


def archive_category_view(request, slug):
    categories = ArchiveCategory.objects.all()
    category = get_object_or_404(ArchiveCategory, slug=slug)
    archive_items = ArchiveItem.objects.filter(category=category).order_by('-id')
    featured_record = ArchiveItem.objects.filter(category=category, is_featured=True).first()
    
    context = {
        'categories': categories,
        'archive_items': archive_items,
        'featured_record': featured_record,
        'active_category': slug,
    }
    return render(request, 'archive_repository.html', context)

# Placeholder views for navigation links referenced in templates
def deadlines_list_view(request):
    return render(request, 'placeholder.html', {
        'title': 'All Deadlines',
        'message': 'All upcoming deadlines will be listed here once the scheduling module is connected.',
    })

def class_detail_view(request, slug):
    course = SimpleNamespace(
        title='Mathematics Structures',
        cover_image=None,
        term='SEM-02',
        difficulty='ADVANCED',
        description='A structured journey through the fields of modern mathematics and structural logic.',
        code='MODULE-042',
    )
    curriculum_modules = [
        SimpleNamespace(title='Topology of Shapes', summary='Properties of space preserved under continuous deformations.'),
        SimpleNamespace(title='Complex Analysis', summary='The investigation of functions of complex numbers.'),
    ]
    assessments = [
        SimpleNamespace(id=1, type='QUIZ', duration_or_due='15 MIN', title='Differential Logic Assessment', description='Rapid fire evaluation of advanced calculus and derivative proofs.'),
        SimpleNamespace(id=2, type='ASSIGNMENT', duration_or_due='DUE FRI', title='Mandelbrot Submission', description='Construct a visual fractal recursion system.'),
    ]
    metrics = {
        'mastery_score': 68,
        'logical_reasoning': 'A+',
        'theoretical_proofs': 'B',
        'computational_accuracy': 'A-',
    }
    return render(request, 'class_detail.html', {
        'course': course,
        'curriculum_modules': curriculum_modules,
        'assessments': assessments,
        'metrics': metrics,
    })


def dossier_archive_view(request):
    return archive_index_view(request)


def teacher_profile_view(request):
    user = request.user if request.user.is_authenticated else None
    instructor = SimpleNamespace(
        name=(user.get_full_name() or user.username) if user else 'Prof. Aris',
        title_role='Lead Instructor',
        bio='Pioneer in the architecture of post-logical frameworks. Bridging classical axiomatic systems with emerging digital metaphysics.',
        established_year=2024,
        avatar=None,
    )
    academic_focus = [
        SimpleNamespace(title='Digital Metaphysics', description='Exploring ontology in recursive computational environments.'),
        SimpleNamespace(title='Algorithmic Semantics', description='Translating formal systems into interpretive structures.'),
    ]
    methodologies = [
        SimpleNamespace(name='Axiomatic Systems Analysis'),
        SimpleNamespace(name='Formal Logic Structures'),
    ]
    manuscripts = [
        SimpleNamespace(publication_year=2024, title='The Ghost in the Code', publisher_tag='Peer Reviewed / Volume IX', file=None),
    ]
    active_cohorts = [
        SimpleNamespace(access_level='FULL ACCESS', name='Neural Architecture II', description='A deep dive into structural patterns of artificial synapses.', member_count=14, is_private=False),
    ]
    context = {
        'instructor': instructor,
        'academic_focus': academic_focus,
        'methodologies': methodologies,
        'manuscripts': manuscripts,
        'active_cohorts': active_cohorts,
        'next_session_date': 'OCTOBER 2026',
    }
    return render(request, 'teacher_profile.html', context)


def student_profile_view(request):
    user = request.user if request.user.is_authenticated else None
    student_name = (user.get_full_name() or user.username) if user else 'Alex Stone'
    student = SimpleNamespace(
        full_name=student_name,
        profile_picture=None,
        enrolled_year=2024,
        rank_title='VANGUARD',
        level=42,
        xp_percentage=88,
        total_hours='1,240',
        manifesto='Education is not the filling of a vessel, but the lighting of a flame.',
        focus_alpha='Neural Architecture',
        focus_beta='Ancient Epigraphy',
    )
    unlocked_titles = [
        SimpleNamespace(slug_name='CYPHER_ADEPT', is_active=False, is_muted=False, is_italic=False),
        SimpleNamespace(slug_name='VOID_WALKER', is_active=True, is_muted=False, is_italic=False),
        SimpleNamespace(slug_name='ARCHIVIST_LVL3', is_active=False, is_muted=True, is_italic=False),
        SimpleNamespace(slug_name='PHILOSOPHICAL_ENGINEER', is_active=False, is_muted=False, is_italic=True),
    ]
    recent_dossiers = [
        SimpleNamespace(title='The Ethics of Synthetic Intuition', published_date=timezone.now(), get_absolute_url='/archive/dossiers/'),
    ]
    return render(request, 'student_profile.html', {
        'student': student,
        'unlocked_titles': unlocked_titles,
        'recent_dossiers': recent_dossiers,
    })


def quiz_detail_view(request, quiz_id):
    quiz = SimpleNamespace(id=quiz_id, title=f'Quiz {quiz_id}')
    question = SimpleNamespace(
        id=1,
        text='Does the architecture of a digital space dictate the morality of its inhabitants?',
        subtext='Consider the implications of algorithmic curation and forced architectural constraints in virtual environments.',
        illustration=None,
    )
    options = [
        SimpleNamespace(id=1, title='Explicit Determinism', description='Architecture creates rigid pathways that eliminate free choice entirely.'),
        SimpleNamespace(id=2, title='Soft Influence', description='Spatial design nudges behavior while leaving room for individual agency.'),
    ]
    return render(request, 'quiz_detail.html', {
        'quiz': quiz,
        'question': question,
        'options': options,
        'session_name': 'ADVANCED LOGIC',
        'current_index': 3,
        'total_questions': 10,
        'time_remaining': '12:45',
    })

@login_required
def submit_assignment_view(request, item_id):
    if request.method == 'POST':
        return redirect('study_dashboard')
    return render(request, 'placeholder.html', {
        'title': 'Submit Assignment',
        'message': 'This assignment submission page is not yet connected to the file upload workflow. Use the student dashboard until the submission module is active.',
    })

@login_required
def submit_quiz_response_view(request, quiz_id):
    if request.method == 'POST':
        return redirect('study_dashboard')
    return redirect('quiz_detail', quiz_id=quiz_id)

def apply_mentorship_view(request):
    return render(request, 'placeholder.html', {
        'title': 'Apply for Mentorship',
        'message': 'Mentorship applications are being built. Complete your profile and check back to submit your request.',
    })