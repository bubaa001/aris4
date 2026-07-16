from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.db import models
from django.utils import timezone
import random
from .forms import RegisterForm, LoginForm
from .models import User, AcademicClass, Module, ClassContent, ArchiveCategory, ArchiveItem, Quiz, Question, Choice, StudentQuizSubmission, LibraryBook, InstructorProfile, StudentProfile, ParentChildLink, Challenge, ChallengeClass, Notification
from sync_manager.triggers import trigger_sync_after_action
from .tiers import get_tier_info, build_xp_context, TIER_COLORS


# HELPER: Quiz Question Results Builder


def build_question_results(submission, questions):
    """Build a list of question result dicts from a submission and its questions."""
    results = []
    for question in questions:
        selected_choice_id = submission.answers.get(str(question.id))
        selected_choice = None
        correct_choice = None
        is_correct = False
        for choice in question.choices.all():
            if choice.is_correct:
                correct_choice = choice
            if selected_choice_id and choice.id == selected_choice_id:
                selected_choice = choice
                is_correct = choice.is_correct
        results.append({
            'question': question,
            'selected_choice': selected_choice,
            'correct_choice': correct_choice,
            'is_correct': is_correct,
        })
    return results



# HELPER: Leaderboard Data


def get_leaderboard_data(request):
    """Build leaderboard context: top 5 students, current user rank, tier list."""
    students = User.objects.filter(role='student').order_by('-xp')

    # Top 5 leaderboard with dense ranking
    top5 = []
    last_xp = None
    rank = 0
    skipped = 0
    for s in students:
        if s.xp != last_xp:
            rank += 1 + skipped
            skipped = 0
        else:
            skipped += 1
        last_xp = s.xp
        level, title, _, _ = get_tier_info(s.xp or 0)
        top5.append({
            'rank': rank,
            'student_id': s.id,
            'username': s.username,
            'xp': s.xp or 0,
            'level': level,
            'title': title,
            'tier_color_class': TIER_COLORS.get(title, 'bg-gray-600 text-white'),
        })
        if len(top5) >= 5:
            break

    # Current user's rank and info (dense rank: count students with MORE xp)
    current_user_rank = None
    tied_count = 0
    xp_gap_to_top = None
    current_user_tier = None
    current_user_tier_color = 'bg-gray-600 text-white'
    if request.user.is_authenticated and request.user.role == 'student':
        user_xp = request.user.xp or 0
        # Dense rank: 1 + number of students with strictly more XP
        higher_count = User.objects.filter(role='student', xp__gt=user_xp).count()
        current_user_rank = higher_count + 1
        # How many are tied at this XP?
        tied_count = User.objects.filter(role='student', xp=user_xp).count() - 1  # minus self
        if top5:
            top_xp = top5[0]['xp']
            xp_gap_to_top = max(0, top_xp - user_xp)
        _, current_user_tier, _, _ = get_tier_info(user_xp)
        current_user_tier_color = TIER_COLORS.get(current_user_tier, 'bg-gray-600 text-white')

    # All tiers definition
    tiers = [
        {'level': 1, 'title': 'Initiate', 'range_min': 0, 'range_max': 500, 'description': 'The beginning of the journey'},
        {'level': 2, 'title': 'Scholar', 'range_min': 500, 'range_max': 1500, 'description': 'Dedicated to the pursuit of knowledge'},
        {'level': 3, 'title': 'Alpha Vanguard', 'range_min': 1500, 'range_max': 3000, 'description': 'Leading the charge in intellectual warfare'},
        {'level': 4, 'title': 'Elite Scholar', 'range_min': 3000, 'range_max': 5000, 'description': 'Among the finest minds in the arena'},
        {'level': 5, 'title': 'Grandmaster', 'range_min': 5000, 'range_max': None, 'description': 'The pinnacle of scholarly dominance'},
    ]

    user_xp = request.user.xp if request.user.is_authenticated else 0
    for tier in tiers:
        tier['is_unlocked'] = user_xp >= tier['range_min']
        if tier['range_max'] is None:
            tier['progress_pct'] = 100 if tier['is_unlocked'] else 0
        else:
            tier_range = tier['range_max'] - tier['range_min']
            clamped = max(0, min(tier['range_max'], user_xp) - tier['range_min'])
            tier['progress_pct'] = int((clamped / tier_range) * 100) if tier_range > 0 else 0

    return {
        'top5_leaderboard': top5,
        'current_user_rank': current_user_rank,
        'tied_count': tied_count,
        'xp_gap_to_top': xp_gap_to_top,
        'current_user_tier': current_user_tier,
        'current_user_tier_color': current_user_tier_color,
        'tiers': tiers,
        'total_students': students.count(),
    }



# VIEWS: Core / Auth

def home_view(request):
    # Redirect authenticated users to their role-specific dashboard
    if request.user.is_authenticated:
        if request.user.role == 'student':
            return redirect('study_dashboard')
        elif request.user.role == 'instructor':
            if request.user.is_approved:
                return redirect('instructor_dashboard')
            else:
                return redirect('pending_approval')
        elif request.user.role == 'parent':
            return redirect('parent_dashboard')
        elif request.user.role == 'admin' or request.user.is_superuser:
            return redirect('admin_dashboard')

    student_count = User.objects.filter(role='student').count()
    instructor_count = User.objects.filter(role='instructor').count()
    class_count = AcademicClass.objects.count()

    top_student = User.objects.filter(role='student').order_by('-xp').first()
    top_student_name = "NO SCHOLARS YET"
    top_student_xp = 0
    active_title = "Initiate"
    active_title_color = 'bg-gray-600 text-white'
    if top_student:
        top_student_name = top_student.username.upper()
        top_student_xp = top_student.xp
        _, active_title, _, _ = get_tier_info(top_student_xp or 0)
        active_title_color = TIER_COLORS.get(active_title, 'bg-gray-600 text-white')

    active_challenges = Challenge.objects.filter(is_active=True).prefetch_related('class_links')[:3]

    # ---------- Previous challenge winner ----------
    prev_challenge_winner = None
    last_ended_challenge = Challenge.objects.filter(is_active=False).order_by('-end_date').first()
    if last_ended_challenge:
        student_ids = User.objects.filter(
            enrolled_classes__in=last_ended_challenge.classes.all(), role='student'
        ).distinct().values_list('id', flat=True)

        best_submission = (
            StudentQuizSubmission.objects.filter(
                student_id__in=student_ids,
                submitted_at__gte=last_ended_challenge.start_date,
                submitted_at__lte=last_ended_challenge.end_date,
            )
            .values('student_id')
            .annotate(total=models.Sum('score'))
            .order_by('-total')
            .first()
        )
        if best_submission:
            student = User.objects.get(id=best_submission['student_id'])
            prev_challenge_winner = {
                'name': student.username,
                'xp': best_submission['total'] or 0,
                'challenge_title': last_ended_challenge.title,
                'challenge_id': last_ended_challenge.id,
            }

    # ---------- Real quiz data for home page ----------
    latest_quiz = Quiz.objects.order_by('-created_at').first()
    total_quizzes = Quiz.objects.count()
    total_submissions = StudentQuizSubmission.objects.count()
    if latest_quiz:
        latest_quiz_submissions = StudentQuizSubmission.objects.filter(quiz=latest_quiz).count()
    else:
        latest_quiz_submissions = 0
    # -----------------------------------------------

    return render(request, 'home.html', {
        'student_count': student_count,
        'instructor_count': instructor_count,
        'class_count': class_count,
        'top_student_name': top_student_name,
        'top_student_xp': top_student_xp,
        'active_title': active_title,
        'active_title_color': active_title_color,
        'active_challenges': active_challenges,
        'prev_challenge_winner': prev_challenge_winner,
        'latest_quiz': latest_quiz,
        'latest_quiz_submissions': latest_quiz_submissions,
        'total_quizzes': total_quizzes,
        'total_submissions': total_submissions,
    })


@ensure_csrf_cookie
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Check for duplicate username before saving
            if User.objects.filter(username=form.cleaned_data['username']).exists():
                form.add_error('username', 'This username is already taken.')
            else:
                try:
                    user = form.save()
                    login(request, user)
                    trigger_sync_after_action()
                    if user.role == 'student':
                        return redirect('select_level')
                    elif user.role == 'instructor':
                        return redirect('pending_approval')
                except Exception:
                    form.add_error('username', 'This username is already taken.')
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
                return redirect('instructor_dashboard' if user.is_approved else 'pending_approval')
            elif user.role == 'parent':
                return redirect('parent_dashboard')
            elif user.role == 'admin' or user.is_superuser:
                return redirect('admin_dashboard')
    else:
        form = LoginForm(request)
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')



# VIEWS: Student


def select_level_view(request):
    """Show all classes that have an instructor assigned, for students to enroll."""
    classes = AcademicClass.objects.filter(instructor__isnull=False)
    enrolled_class_ids = []
    if request.user.is_authenticated:
        enrolled_class_ids = list(request.user.enrolled_classes.values_list('id', flat=True))

    if request.method == 'POST' and request.user.is_authenticated:
        class_id = request.POST.get('class_id')
        action = request.POST.get('action')
        if class_id and action == 'enroll':
            academic_class = get_object_or_404(AcademicClass, id=class_id)
            if request.user not in academic_class.students.all():
                academic_class.students.add(request.user)
            return redirect('study_dashboard')
        elif class_id and action == 'unenroll':
            academic_class = get_object_or_404(AcademicClass, id=class_id)
            academic_class.students.remove(request.user)
            return redirect('select_level')

    return render(request, 'select_level.html', {
        'classes': classes,
        'enrolled_class_ids': enrolled_class_ids,
    })


@login_required
def student_dashboard_view(request):
    user = request.user
    current_xp = user.xp if hasattr(user, 'xp') else 0
    xp_context = build_xp_context(current_xp)

    academic_status = {
        'semester_label': 'Spring Semester',
        'current_week': '08',
        **xp_context,
    }

    return render(request, 'student_dashboard.html', {
        'current_student': user,
        'academic_status': academic_status,
        'enrolled_classes': AcademicClass.objects.filter(students=user),
    })


@login_required
def student_class_view(request, slug):
    """Student views a class they're enrolled in, sees content and quizzes grouped by module."""
    academic_class = get_object_or_404(AcademicClass, slug=slug)
    if request.user not in academic_class.students.all() and request.user.role != 'instructor':
        return redirect('study_dashboard')

    quizzes = academic_class.quizzes.all()
    submissions = StudentQuizSubmission.objects.filter(student=request.user, quiz__in=quizzes)
    submission_map = {s.quiz_id: s for s in submissions}

    modules = academic_class.modules.prefetch_related(
        models.Prefetch('contents', queryset=ClassContent.objects.all()),
        models.Prefetch('quizzes', queryset=Quiz.objects.prefetch_related('questions')),
    ).all()

    module_data = []
    for module in modules:
        module_quiz_data = []
        for quiz in module.quizzes.all():
            sub = submission_map.get(quiz.id)
            module_quiz_data.append({
                'quiz': quiz,
                'submission': sub,
                'has_submitted': sub is not None,
            })
        module_data.append({
            'module': module,
            'contents': module.contents.all(),
            'quiz_data': module_quiz_data,
        })

    orphaned_contents = academic_class.contents.filter(module__isnull=True)
    orphaned_quizzes = academic_class.quizzes.filter(module__isnull=True)
    orphaned_quiz_data = [
        {'quiz': quiz, 'submission': submission_map.get(quiz.id), 'has_submitted': submission_map.get(quiz.id) is not None}
        for quiz in orphaned_quizzes
    ]

    return render(request, 'student_class_detail.html', {
        'class': academic_class,
        'module_data': module_data,
        'orphaned_contents': orphaned_contents,
        'orphaned_quiz_data': orphaned_quiz_data,
    })


@login_required
def student_profile_view(request, username=None):
    """View a student's profile. If no username given, shows the logged-in user's own profile."""
    if username:
        student = get_object_or_404(User, username=username, role='student')
        is_own = (request.user == student)
    else:
        student = request.user
        is_own = True

    # Handle invite link generation
    parent_link = None
    active_links = ParentChildLink.objects.filter(child=student, parent__isnull=False, is_active=True)
    max_parents_reached = active_links.count() >= 2
    pending_link = ParentChildLink.objects.filter(child=student, parent__isnull=True).first()

    if is_own and request.method == 'POST' and request.POST.get('action') == 'generate_invite':
        if max_parents_reached:
            from django.contrib import messages
            messages.error(request, 'Maximum of 2 parents already connected.')
        elif not pending_link:
            parent_link = ParentChildLink.objects.create(child=student)
            parent_link.save()  # ensures link_code is generated
            pending_link = parent_link

    # Regenerate link if requested
    if is_own and request.method == 'POST' and request.POST.get('action') == 'regenerate_invite':
        if pending_link:
            pending_link.delete()
        pending_link = ParentChildLink.objects.create(child=student)

    current_xp = student.xp or 0
    xp_ctx = build_xp_context(current_xp)
    rank_title = xp_ctx['tier_title']
    level = xp_ctx['current_level']
    xp_to_next = xp_ctx['xp_to_next']
    xp_percentage = xp_ctx['xp_percentage']
    tier_color_class = TIER_COLORS.get(rank_title, 'bg-gray-600 text-white')

    enrolled_classes = AcademicClass.objects.filter(students=student)
    student_name = student.get_full_name() or student.username

    # Student profile info (optional fields)
    profile = StudentProfile.objects.filter(user=student).first()

    # Build tiers list for the journey visualization
    tiers = [
        {'level': 1, 'title': 'Initiate', 'range_min': 0, 'range_max': 500},
        {'level': 2, 'title': 'Scholar', 'range_min': 500, 'range_max': 1500},
        {'level': 3, 'title': 'Alpha Vanguard', 'range_min': 1500, 'range_max': 3000},
        {'level': 4, 'title': 'Elite Scholar', 'range_min': 3000, 'range_max': 5000},
        {'level': 5, 'title': 'Grandmaster', 'range_min': 5000, 'range_max': None},
    ]
    for tier in tiers:
        tier['is_unlocked'] = current_xp >= tier['range_min']

    return render(request, 'student_profile.html', {
        'profile_user': student,
        'student_profile': profile,
        'student': {
            'full_name': student_name,
            'rank_title': rank_title,
            'level': level,
            'xp_percentage': xp_percentage,
            'xp_to_next': xp_to_next,
            'xp': current_xp,
            'tier_color_class': tier_color_class,
        },
        'is_own_profile': is_own,
        'enrolled_classes': enrolled_classes,
        'enrolled_count': enrolled_classes.count(),
        'tiers': tiers,
        'active_links': active_links,
        'pending_link': pending_link,
        'max_parents_reached': max_parents_reached,
    })


@login_required
def edit_student_profile_view(request):
    """Create or edit a student's profile."""
    if request.user.role != 'student':
        return redirect('home')

    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        if request.FILES.get('avatar'):
            profile.avatar = request.FILES['avatar']
        profile.bio = request.POST.get('bio', '').strip()
        profile.inspire_message = request.POST.get('inspire_message', '').strip()
        profile.favorite_quote = request.POST.get('favorite_quote', '').strip()
        profile.parent_names = [n.strip() for n in request.POST.getlist('parent_name') if n.strip()]
        profile.save()
        return redirect('student_profile')

    return render(request, 'edit_student_profile.html', {'profile': profile})


# VIEWS: Instructor


def instructor_dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.role != 'instructor':
        return redirect('home')
    if not request.user.is_approved:
        return redirect('pending_approval')

    return render(request, 'instructor_dashboard.html', {
        'my_classes': AcademicClass.objects.filter(instructor=request.user),
    })


def pending_approval_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.role != 'instructor':
        return redirect('home')
    if request.user.is_approved:
        return redirect('instructor_dashboard')
    return render(request, 'pending_approval.html')


@login_required
def instructor_manage_classes_view(request):
    if request.user.role != 'instructor':
        return redirect('home')
    if not request.user.is_approved:
        return redirect('pending_approval')

    if request.method == 'POST':
        action = request.POST.get('action')

        # Handle class creation
        if action == 'create':
            code = request.POST.get('code', '').strip()
            title = request.POST.get('title', '').strip()
            if code and title:
                from django.utils.text import slugify
                slug = slugify(code)
                base_slug = slug
                counter = 1
                while AcademicClass.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                AcademicClass.objects.create(
                    code=code, title=title,
                    schedule_string=request.POST.get('schedule_string', '').strip() or 'TBD',
                    meeting_link=request.POST.get('meeting_link', '').strip(),
                    slug=slug, instructor=request.user,
                )
            return redirect('instructor_manage_classes')

        # Handle assign/remove
        class_id = request.POST.get('class_id')
        if class_id:
            academic_class = get_object_or_404(AcademicClass, id=class_id)
            if action == 'assign' and (academic_class.instructor is None or academic_class.instructor == request.user):
                academic_class.instructor = request.user
                academic_class.save(update_fields=['instructor'])
            elif action == 'remove' and academic_class.instructor == request.user:
                academic_class.instructor = None
                academic_class.save(update_fields=['instructor'])
        return redirect('instructor_manage_classes')

    return render(request, 'instructor_manage_classes.html', {
        'available_classes': AcademicClass.objects.filter(
            models.Q(instructor__isnull=True) | models.Q(instructor=request.user)
        ),
        'my_classes': AcademicClass.objects.filter(instructor=request.user),
    })


@login_required
def instructor_class_view(request, slug):
    """Instructor manages a class: adds modules, content, creates quizzes."""
    if request.user.role != 'instructor':
        return redirect('home')

    academic_class = get_object_or_404(AcademicClass, slug=slug, instructor=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        # Module actions
        if action == 'add_module':
            title = request.POST.get('module_title', '').strip()
            if title:
                last_order = academic_class.modules.aggregate(max_order=models.Max('order'))['max_order'] or 0
                Module.objects.create(academic_class=academic_class, title=title, order=last_order + 1)
            return redirect('instructor_class', slug=slug)

        if action == 'edit_module':
            module_id = request.POST.get('module_id')
            new_title = request.POST.get('module_title', '').strip()
            if module_id and new_title:
                Module.objects.filter(id=module_id, academic_class=academic_class).update(title=new_title)
            return redirect('instructor_class', slug=slug)

        if action == 'delete_module':
            module_id = request.POST.get('module_id')
            if module_id:
                Module.objects.filter(id=module_id, academic_class=academic_class).delete()
            return redirect('instructor_class', slug=slug)

        # Content actions
        if action == 'add_content':
            title = request.POST.get('title', '').strip()
            if title:
                content = ClassContent.objects.create(
                    academic_class=academic_class, title=title,
                    description=request.POST.get('description', '').strip(),
                )
                module_id = request.POST.get('module_id')
                if module_id:
                    content.module_id = module_id
                    content.save(update_fields=['module_id'])
            return redirect('instructor_class', slug=slug)

        if action == 'edit_content':
            content_id = request.POST.get('content_id')
            new_title = request.POST.get('content_title', '').strip()
            new_desc = request.POST.get('content_description', '').strip()
            if content_id:
                ClassContent.objects.filter(id=content_id, academic_class=academic_class).update(
                    title=new_title,
                    description=new_desc,
                )
            return redirect('instructor_class', slug=slug)

        if action == 'delete_content':
            content_id = request.POST.get('content_id')
            if content_id:
                ClassContent.objects.filter(id=content_id, academic_class=academic_class).delete()
            return redirect('instructor_class', slug=slug)

        # Quiz actions
        if action == 'create_quiz':
            title = request.POST.get('quiz_title', '').strip()
            if title:
                quiz = Quiz.objects.create(
                    title=title, description=request.POST.get('quiz_description', '').strip(),
                    creator=request.user, academic_class=academic_class,
                )
                module_id = request.POST.get('module_id')
                if module_id:
                    quiz.module_id = module_id
                    quiz.save(update_fields=['module_id'])

                question_texts = request.POST.getlist('question_text[]')
                for qi, qtext in enumerate(question_texts):
                    if not qtext.strip():
                        continue
                    question = Question.objects.create(quiz=quiz, text=qtext.strip(), order=qi)
                    choice_texts = request.POST.getlist(f'choice_text_{qi}[]')
                    correct_choice = request.POST.get(f'correct_choice_{qi}')
                    has_correct = False
                    for ci, ctext in enumerate(choice_texts):
                        if not ctext.strip():
                            continue
                        is_correct = (str(ci) == correct_choice)
                        if is_correct:
                            has_correct = True
                        Choice.objects.create(question=question, text=ctext.strip(), is_correct=is_correct, order=ci)
                    if not has_correct:
                        first_choice = question.choices.first()
                        if first_choice:
                            first_choice.is_correct = True
                            first_choice.save(update_fields=['is_correct'])
            return redirect('instructor_class', slug=slug)

        if action == 'edit_quiz':
            quiz_id = request.POST.get('quiz_id')
            new_title = request.POST.get('quiz_title', '').strip()
            new_desc = request.POST.get('quiz_description', '').strip()
            if quiz_id:
                Quiz.objects.filter(id=quiz_id, academic_class=academic_class).update(
                    title=new_title,
                    description=new_desc,
                )
            return redirect('instructor_class', slug=slug)

        if action == 'delete_quiz':
            quiz_id = request.POST.get('quiz_id')
            if quiz_id:
                Quiz.objects.filter(id=quiz_id, academic_class=academic_class).delete()
            return redirect('instructor_class', slug=slug)

    modules = academic_class.modules.prefetch_related(
        models.Prefetch('contents', queryset=ClassContent.objects.all()),
        models.Prefetch('quizzes', queryset=Quiz.objects.prefetch_related('questions__choices', 'submissions')),
    ).all()

    orphaned_contents = academic_class.contents.filter(module__isnull=True)
    orphaned_quizzes = academic_class.quizzes.filter(module__isnull=True)

    # Build student quiz stats
    all_quizzes = list(academic_class.quizzes.all())
    all_submissions = StudentQuizSubmission.objects.filter(quiz__in=all_quizzes).select_related('student')

    student_stats = {}
    for student in academic_class.students.all():
        student_stats[student.id] = {
            'student': student, 'total_quizzes': len(all_quizzes),
            'completed_quizzes': 0, 'total_score': 0, 'total_possible': 0, 'submissions': [],
        }
    for sub in all_submissions:
        if sub.student_id in student_stats:
            stats = student_stats[sub.student_id]
            stats['completed_quizzes'] += 1
            stats['total_score'] += sub.score
            stats['total_possible'] += sub.total
            stats['submissions'].append(sub)

    student_list = sorted(student_stats.values(), key=lambda s: (-s['completed_quizzes'], -s['total_score'] if s['total_possible'] > 0 else 0))

    # Aggregate stats for summary cards
    total_students = len(student_list)
    total_completed_all = sum(s['completed_quizzes'] for s in student_list)
    total_score_all = sum(s['total_score'] for s in student_list)
    total_possible_all = sum(s['total_possible'] for s in student_list)
    avg_completion_pct = int((total_completed_all / (total_students * len(all_quizzes))) * 100) if total_students > 0 and len(all_quizzes) > 0 else 0
    class_avg_pct = int((total_score_all / total_possible_all) * 100) if total_possible_all > 0 else 0

    return render(request, 'instructor_class_detail.html', {
        'class': academic_class, 'modules': modules,
        'orphaned_contents': orphaned_contents, 'orphaned_quizzes': orphaned_quizzes,
        'student_list': student_list,
        'total_students': total_students,
        'avg_completion_pct': avg_completion_pct,
        'class_avg_pct': class_avg_pct,
    })


@login_required
def instructor_student_directory_view(request, slug):
    """Dedicated searchable student directory for a class (handles 200+ students)."""
    if request.user.role != 'instructor':
        return redirect('home')

    academic_class = get_object_or_404(AcademicClass, slug=slug, instructor=request.user)
    search_query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'name')

    all_quizzes = list(academic_class.quizzes.all())
    all_submissions = StudentQuizSubmission.objects.filter(quiz__in=all_quizzes).select_related('student')

    student_stats = {}
    for student in academic_class.students.all():
        student_stats[student.id] = {
            'student': student,
            'total_quizzes': len(all_quizzes),
            'completed_quizzes': 0,
            'total_score': 0,
            'total_possible': 0,
        }
    for sub in all_submissions:
        if sub.student_id in student_stats:
            stats = student_stats[sub.student_id]
            stats['completed_quizzes'] += 1
            stats['total_score'] += sub.score
            stats['total_possible'] += sub.total

    student_list = list(student_stats.values())

    # Apply search filter
    if search_query:
        q = search_query.lower()
        student_list = [
            s for s in student_list
            if q in s['student'].username.lower()
            or q in (s['student'].get_full_name() or '').lower()
            or q in (s['student'].email or '').lower()
        ]

    # Apply sorting
    if sort_by == 'name':
        student_list.sort(key=lambda s: (s['student'].get_full_name() or s['student'].username).lower())
    elif sort_by == 'completion':
        student_list.sort(key=lambda s: (-s['completed_quizzes'], -s['total_score']))
    elif sort_by == 'score':
        student_list.sort(key=lambda s: (
            -(s['total_score'] / s['total_possible']) if s['total_possible'] > 0 else 0,
        ))
    elif sort_by == 'xp':
        student_list.sort(key=lambda s: -(s['student'].xp or 0))

    total_count = len(student_stats)
    filtered_count = len(student_list)

    return render(request, 'instructor_student_directory.html', {
        'class': academic_class,
        'student_list': student_list,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_count': total_count,
        'filtered_count': filtered_count,
    })



# VIEWS: Instructor Profile


@login_required
def teacher_profile_view(request, username=None):
    """View an instructor's profile."""
    if username:
        instructor = get_object_or_404(User, username=username, role='instructor')
        profile = InstructorProfile.objects.filter(user=instructor).first()
        if not profile or not profile.has_profile():
            return render(request, 'teacher_profile.html', {
                'profile': None, 'instructor_user': instructor,
                'active_cohorts': [], 'is_own_profile': request.user == instructor,
            })
        taught_classes = AcademicClass.objects.filter(instructor=instructor)
    else:
        if request.user.role != 'instructor':
            return redirect('home')
        instructor = request.user
        profile = InstructorProfile.objects.filter(user=instructor).first()
        if not profile or not profile.has_profile():
            return redirect('edit_instructor_profile')
        taught_classes = AcademicClass.objects.filter(instructor=instructor)

    active_cohorts = [
        {
            'code': cls.code,
            'name': cls.title,
            'schedule': cls.schedule_string,
            'member_count': cls.students.count(),
            'slug': cls.slug,
        }
        for cls in taught_classes
    ]

    total_students = sum(c['member_count'] for c in active_cohorts)

    return render(request, 'teacher_profile.html', {
        'profile': profile, 'instructor_user': instructor,
        'active_cohorts': active_cohorts, 'is_own_profile': request.user == instructor,
        'total_students': total_students,
    })


@login_required
def edit_instructor_profile_view(request):
    """Create or edit an instructor's profile."""
    if request.user.role != 'instructor':
        return redirect('home')

    profile, _ = InstructorProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        profile.title_role = request.POST.get('title_role', '').strip()
        profile.bio = request.POST.get('bio', '').strip()
        if request.FILES.get('avatar'):
            profile.avatar = request.FILES['avatar']
        established = request.POST.get('established_year', '').strip()
        if established:
            profile.established_year = int(established)

        # Process academic focus (JSON)
        focus_titles = request.POST.getlist('focus_title[]')
        focus_descriptions = request.POST.getlist('focus_description[]')
        profile.academic_focus = [
            {'title': t.strip(), 'description': focus_descriptions[i].strip() if i < len(focus_descriptions) else ''}
            for i, t in enumerate(focus_titles) if t.strip()
        ]

        # Process methodologies (JSON)
        profile.methodologies = [{'name': n.strip()} for n in request.POST.getlist('method_name[]') if n.strip()]

        # Process manuscripts (JSON)
        manuscript_years = request.POST.getlist('manuscript_year[]')
        manuscript_titles = request.POST.getlist('manuscript_title[]')
        manuscript_tags = request.POST.getlist('manuscript_tag[]')
        profile.manuscripts = [
            {
                'publication_year': int(manuscript_years[i]) if i < len(manuscript_years) and manuscript_years[i].strip() else 2024,
                'title': t.strip(),
                'publisher_tag': manuscript_tags[i].strip() if i < len(manuscript_tags) else '',
            }
            for i, t in enumerate(manuscript_titles) if t.strip()
        ]

        profile.save()
        return redirect('teacher_profile')

    return render(request, 'edit_instructor_profile.html', {'profile': profile})



# VIEWS: Parent


@login_required
def parent_dashboard_view(request):
    """Parent dashboard showing all linked children's overview."""
    if request.user.role != 'parent':
        return redirect('home')

    links = ParentChildLink.objects.filter(parent=request.user, is_active=True).select_related('child')

    children_data = []
    for link in links:
        child = link.child
        enrolled_classes = AcademicClass.objects.filter(students=child)
        submissions = StudentQuizSubmission.objects.filter(student=child)
        total_score = sum(s.score for s in submissions)
        total_possible = sum(s.total for s in submissions)
        avg_pct = int((total_score / total_possible) * 100) if total_possible > 0 else 0

        children_data.append({
            'link': link,
            'student': child,
            'enrolled_count': enrolled_classes.count(),
            'enrolled_classes': enrolled_classes,
            'quiz_count': submissions.count(),
            'total_score': total_score,
            'total_possible': total_possible,
            'avg_pct': avg_pct,
        })

    return render(request, 'parent_dashboard.html', {
        'children_data': children_data,
    })


@login_required
def parent_child_detail_view(request, student_id):
    """Parent views a specific child's full academic overview."""
    if request.user.role != 'parent':
        return redirect('home')

    link = get_object_or_404(ParentChildLink, parent=request.user, child_id=student_id, is_active=True)
    child = link.child

    enrolled_classes = AcademicClass.objects.filter(students=child)

    classes_data = []
    for cls in enrolled_classes:
        quizzes = cls.quizzes.all()
        submissions = StudentQuizSubmission.objects.filter(student=child, quiz__in=quizzes)
        submission_map = {s.quiz_id: s for s in submissions}
        quiz_data = []
        for quiz in quizzes:
            sub = submission_map.get(quiz.id)
            quiz_data.append({
                'quiz': quiz,
                'submission': sub,
                'has_submitted': sub is not None,
            })
        classes_data.append({
            'class': cls,
            'quiz_data': quiz_data,
            'total_quizzes': quizzes.count(),
            'completed_quizzes': submissions.count(),
            'total_score': sum(s.score for s in submissions),
            'total_possible': sum(s.total for s in submissions),
        })

    current_xp = child.xp or 0
    xp_ctx = build_xp_context(current_xp)

    return render(request, 'parent_child_detail.html', {
        'link': link,
        'child': child,
        'classes_data': classes_data,
        'xp_ctx': xp_ctx,
        'tier_color_class': TIER_COLORS.get(xp_ctx['tier_title'], 'bg-gray-600 text-white'),
    })


@login_required
def parent_child_quiz_result_view(request, student_id, quiz_id):
    """Parent views a child's specific quiz result with question breakdown."""
    if request.user.role != 'parent':
        return redirect('home')

    link = get_object_or_404(ParentChildLink, parent=request.user, child_id=student_id, is_active=True)
    child = link.child
    quiz = get_object_or_404(Quiz, id=quiz_id)
    submission = get_object_or_404(StudentQuizSubmission, student=child, quiz=quiz)
    questions = quiz.questions.prefetch_related('choices').all()

    return render(request, 'parent_quiz_result.html', {
        'child': child,
        'quiz': quiz,
        'submission': submission,
        'results': build_question_results(submission, questions),
    })


# VIEWS: Parent Registration (no login required)


def parent_register_view(request, link_code):
    """Registration page for parents coming from an invite link."""
    link = get_object_or_404(ParentChildLink, link_code=link_code, parent__isnull=True, is_active=True)

    # Check max parents limit (2)
    active_count = ParentChildLink.objects.filter(child=link.child, parent__isnull=False, is_active=True).count()
    if active_count >= 2:
        return render(request, 'parent_register.html', {
            'form': None,
            'child_name': link.child.get_full_name() or link.child.username,
            'link_code': link_code,
            'max_reached': True,
        })

    if request.method == 'POST':
        from .forms import ParentRegisterForm
        form = ParentRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'parent'
            user.is_approved = True
            user.save()
            # Link the parent to the child
            link.parent = user
            link.linked_at = timezone.now()
            link.save()
            login(request, user)
            return redirect('parent_dashboard')
    else:
        from .forms import ParentRegisterForm
        form = ParentRegisterForm()

    return render(request, 'parent_register.html', {
        'form': form,
        'child_name': link.child.get_full_name() or link.child.username,
        'link_code': link_code,
    })


# VIEWS: Admin


@login_required
def admin_dashboard_view(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden('Not authorized')

    students = User.objects.filter(role='student')
    total_xp = sum(s.xp or 0 for s in students)
    top_student = students.order_by('-xp').first()

    # Build class stats for per-group reset
    all_classes = AcademicClass.objects.filter(students__isnull=False).distinct()
    class_data = []
    for cls in all_classes:
        class_xp = sum(s.xp or 0 for s in cls.students.all())
        class_data.append({
            'id': cls.id,
            'code': cls.code,
            'title': cls.title,
            'student_count': cls.students.count(),
            'total_xp': class_xp,
        })

    return render(request, 'admin_approval.html', {
        'pending_instructors': User.objects.filter(role='instructor', is_approved=False),
        'approved_instructors': User.objects.filter(role='instructor', is_approved=True),
        'total_students': students.count(),
        'total_xp': total_xp,
        'top_student_name': top_student.get_full_name() or top_student.username if top_student else 'N/A',
        'top_student_xp': top_student.xp if top_student else 0,
        'class_data': class_data,
        'all_classes': AcademicClass.objects.all(),
        'all_challenges': Challenge.objects.all().prefetch_related('class_links'),
    })


@login_required
def admin_reset_xp_view(request):
    """Reset all student XP to 0 (season/event end)."""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden('Not authorized')
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    action = request.POST.get('action', '')
    students = User.objects.filter(role='student')

    if action == 'reset_all':
        count = students.update(xp=0)
        return JsonResponse({'status': 'ok', 'message': f'Reset {count} students XP to 0.', 'count': count})

    if action == 'reset_class':
        class_id = request.POST.get('class_id')
        if class_id:
            cls = get_object_or_404(AcademicClass, id=class_id)
            count = cls.students.update(xp=0)
            return JsonResponse({'status': 'ok', 'message': f'Reset {count} students in {cls.code} XP to 0.', 'count': count})

    return JsonResponse({'status': 'error', 'message': 'Invalid action.'}, status=400)


@login_required
def admin_challenge_create_view(request):
    """Admin creates a new challenge event."""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden('Not authorized')
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    title = request.POST.get('title', '').strip()
    if title:
        from django.utils import timezone
        challenge = Challenge.objects.create(
            title=title,
            description=request.POST.get('description', '').strip(),
            rules=request.POST.get('rules', '').strip(),
            created_by=request.user,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=int(request.POST.get('days', 7))),
            prize_pool_xp=int(request.POST.get('prize_xp', 0) or 0),
        )
        # Attach selected classes
        class_ids = request.POST.getlist('class_ids')
        for cid in class_ids:
            cls = AcademicClass.objects.filter(id=cid).first()
            if cls and not ChallengeClass.objects.filter(challenge=challenge, academic_class=cls).exists():
                ChallengeClass.objects.create(challenge=challenge, academic_class=cls)

        # Send email invites to instructors of selected classes
        try:
            from django.core.mail import send_mail
            invited_instructors = set()
            for cid in class_ids:
                cls = AcademicClass.objects.filter(id=cid).select_related('instructor').first()
                if cls and cls.instructor and cls.instructor.email:
                    if cls.instructor.id not in invited_instructors:
                        invited_instructors.add(cls.instructor.id)
                        send_mail(
                            f'Challenge Invite: {title} - aris4.0',
                            f'Dear {cls.instructor.username},\n\n'
                            f'You have been invited to set quizzes for the challenge "{title}".\n\n'
                            f'Description: {request.POST.get("description", "").strip()}\n'
                            f'Duration: {int(request.POST.get("days", 7))} days\n\n'
                            f'Log in to your dashboard to participate.\n\n'
                            f'https://crusader-easing-overlying.ngrok-free.dev/instructor-dashboard/\n\n'
                            f'Best regards,\nThe aris4.0 Team',
                            None, [cls.instructor.email], fail_silently=True
                        )
        except Exception:
            pass  # Email failures shouldn't block challenge creation
    return redirect('admin_dashboard')


@login_required
def admin_challenge_toggle_view(request, challenge_id):
    """Activate/deactivate a challenge."""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden('Not authorized')
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')
    challenge = get_object_or_404(Challenge, id=challenge_id)
    challenge.is_active = not challenge.is_active
    challenge.save(update_fields=['is_active'])
    return redirect('admin_dashboard')


@login_required
def admin_challenge_delete_view(request, challenge_id):
    """Permanently delete a challenge and all its quizzes/questions."""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden('Not authorized')
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')
    challenge = get_object_or_404(Challenge, id=challenge_id)
    challenge.delete()
    return redirect('admin_dashboard')


@login_required
def admin_challenge_award_view(request, challenge_id):
    """Award prizes: all participants +10 XP, top 3 split pool."""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden('Not authorized')
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    challenge = get_object_or_404(Challenge, id=challenge_id)

    # Get leaderboard data (reuse leaderboard logic)
    student_ids = User.objects.filter(
        enrolled_classes__in=challenge.classes.all(), role='student'
    ).distinct().values_list('id', flat=True)

    submissions = StudentQuizSubmission.objects.filter(
        student_id__in=student_ids,
        submitted_at__gte=challenge.start_date,
        submitted_at__lte=challenge.end_date,
    ).values('student_id').annotate(
        total_score=models.Sum('score'),
    ).order_by('-total_score')

    # Build ranked list (only students who actually submitted)
    ranked = [(User.objects.get(id=s['student_id']), s['total_score']) for s in submissions]

    par_bonus = 10
    pool = challenge.prize_pool_xp or 0
    first_pct, second_pct, third_pct = 0.5, 0.3, 0.2

    awarded = 0
    # Only students who solved at least one quiz get +10 XP
    for student, _ in ranked:
        student.xp = (student.xp or 0) + par_bonus
        student.save(update_fields=['xp'])
        awarded += par_bonus

    # Top 3 split pool
    if pool > 0 and len(ranked) >= 1:
        splits = [
            (ranked[0][0], int(pool * first_pct)) if len(ranked) >= 1 else None,
            (ranked[1][0], int(pool * second_pct)) if len(ranked) >= 2 else None,
            (ranked[2][0], int(pool * third_pct)) if len(ranked) >= 3 else None,
        ]
        for s, bonus in [x for x in splits if x]:
            s.xp = (s.xp or 0) + bonus
            s.save(update_fields=['xp'])
            awarded += bonus

    challenge.is_active = False
    challenge.save(update_fields=['is_active'])

    return redirect('admin_dashboard')


@login_required
def admin_instructor_progress_view(request, instructor_id):
    """Admin views a specific instructor's teaching progress."""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden('Not authorized')

    instructor = get_object_or_404(User, id=instructor_id, role='instructor')
    classes = AcademicClass.objects.filter(instructor=instructor)

    class_stats = []
    for cls in classes:
        quizzes = cls.quizzes.count()
        contents = cls.contents.count()
        submissions = StudentQuizSubmission.objects.filter(quiz__academic_class=cls).count()
        students = cls.students.count()
        total_xp = sum(s.xp or 0 for s in cls.students.all())
        class_stats.append({
            'class': cls,
            'quiz_count': quizzes,
            'content_count': contents,
            'submission_count': submissions,
            'student_count': students,
            'total_xp': total_xp,
        })

    return render(request, 'admin_instructor_progress.html', {
        'instructor': instructor,
        'class_stats': class_stats,
        'total_classes': classes.count(),
        'total_students': sum(c['student_count'] for c in class_stats),
    })


def challenge_leaderboard_view(request, challenge_id):
    """Public leaderboard for a specific challenge."""
    challenge = get_object_or_404(Challenge, id=challenge_id)
    # Get all students in challenge classes
    student_ids = User.objects.filter(
        enrolled_classes__in=challenge.classes.all(), role='student'
    ).distinct().values_list('id', flat=True)

    # Get quiz submissions during challenge period
    submissions = StudentQuizSubmission.objects.filter(
        student_id__in=student_ids,
        submitted_at__gte=challenge.start_date,
        submitted_at__lte=challenge.end_date,
    ).values('student_id').annotate(
        total_score=models.Sum('score'),
        total_possible=models.Sum('total'),
        quiz_count=models.Count('id'),
    ).order_by('-total_score')

    leaderboard = []
    rank = 1
    for entry in submissions[:50]:
        student = User.objects.get(id=entry['student_id'])
        pct = int((entry['total_score'] / entry['total_possible']) * 100) if entry['total_possible'] > 0 else 0
        leaderboard.append({
            'rank': rank,
            'student': student,
            'score': entry['total_score'],
            'possible': entry['total_possible'],
            'percentage': pct,
            'quizzes': entry['quiz_count'],
        })
        rank += 1

    return render(request, 'challenge_leaderboard.html', {
        'challenge': challenge,
        'leaderboard': leaderboard,
    })


# ── INSTRUCTOR CHALLENGE VIEWS ──

@login_required
def instructor_challenges_view(request):
    """Show all challenges linked to the instructor's classes."""
    if request.user.role != 'instructor' or not request.user.is_approved:
        return redirect('home')

    my_classes = AcademicClass.objects.filter(instructor=request.user)
    challenges = Challenge.objects.filter(
        classes__in=my_classes, is_active=True
    ).distinct().prefetch_related('classes', 'quizzes')

    # Annotate each challenge with quiz count for this instructor
    challenge_data = []
    for ch in challenges:
        my_quizzes = ch.quizzes.filter(creator=request.user)
        challenge_data.append({
            'challenge': ch,
            'my_quiz_count': my_quizzes.count(),
            'my_classes': my_classes.filter(challenges=ch),
            'status': ch.status,
        })

    return render(request, 'instructor_challenges.html', {
        'challenge_data': challenge_data,
    })


@login_required
def instructor_challenge_detail_view(request, challenge_id):
    """Instructor manages quizzes for a specific challenge."""
    if request.user.role != 'instructor' or not request.user.is_approved:
        return redirect('home')

    challenge = get_object_or_404(Challenge, id=challenge_id)
    my_classes = AcademicClass.objects.filter(instructor=request.user, challenges=challenge)

    if not my_classes.exists():
        return HttpResponseForbidden('Your classes are not part of this challenge.')

    my_quizzes = challenge.quizzes.filter(creator=request.user)

    # Handle quiz creation
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_quiz':
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            class_id = request.POST.get('academic_class_id')
            if title and class_id:
                academic_class = get_object_or_404(AcademicClass, id=class_id, instructor=request.user)
                quiz = Quiz.objects.create(
                    title=title,
                    description=description,
                    creator=request.user,
                    academic_class=academic_class,
                    challenge=challenge,
                )
                return redirect('instructor_challenge_detail', challenge_id=challenge.id)
        elif action == 'add_question':
            quiz_id = request.POST.get('quiz_id')
            quiz = get_object_or_404(Quiz, id=quiz_id, creator=request.user)
            question_text = request.POST.get('question_text', '').strip()
            if question_text:
                order = quiz.questions.count() + 1
                question = Question.objects.create(
                    quiz=quiz,
                    text=question_text,
                    order=order,
                )
                # Create choices
                for i in range(1, 5):
                    choice_text = request.POST.get(f'choice_{i}', '').strip()
                    if choice_text:
                        Choice.objects.create(
                            question=question,
                            text=choice_text,
                            is_correct=(request.POST.get(f'is_correct') == str(i)),
                            order=i,
                        )
                return redirect('instructor_challenge_detail', challenge_id=challenge.id)

    # Build quiz data with question counts
    quiz_data = []
    for quiz in my_quizzes:
        quiz_data.append({
            'quiz': quiz,
            'question_count': quiz.questions.count(),
            'submission_count': StudentQuizSubmission.objects.filter(quiz=quiz).count(),
        })

    return render(request, 'instructor_challenge_detail.html', {
        'challenge': challenge,
        'my_classes': my_classes,
        'quiz_data': quiz_data,
    })


@login_required
def instructor_delete_question_view(request, question_id):
    """Delete a question from a challenge quiz."""
    if request.user.role != 'instructor':
        return redirect('home')
    question = get_object_or_404(Question, id=question_id, quiz__creator=request.user)
    challenge_id = question.quiz.challenge_id
    question.delete()
    if challenge_id:
        return redirect('instructor_challenge_detail', challenge_id=challenge_id)
    return redirect('instructor_dashboard')


# ── STUDENT CHALLENGE VIEWS ──

@login_required
def student_challenges_view(request):
    """Show active challenges for student's enrolled classes."""
    if request.user.role != 'student':
        return redirect('home')

    my_classes = request.user.enrolled_classes.all()
    now = timezone.now()
    challenges = Challenge.objects.filter(
        classes__in=my_classes, is_active=True, start_date__lte=now, end_date__gte=now
    ).distinct().prefetch_related('quizzes')

    challenge_data = []
    for ch in challenges:
        # Quizzes available for this challenge
        ch_quizzes = ch.quizzes.all()
        submitted_count = StudentQuizSubmission.objects.filter(
            student=request.user, quiz__in=ch_quizzes
        ).count()
        challenge_data.append({
            'challenge': ch,
            'total_quizzes': ch_quizzes.count(),
            'submitted_count': submitted_count,
        })

    return render(request, 'student_challenges.html', {
        'challenge_data': challenge_data,
    })


@login_required
def student_challenge_detail_view(request, challenge_id):
    """Student views challenge info, takes quizzes, and sees leaderboard."""
    if request.user.role != 'student':
        return redirect('home')

    challenge = get_object_or_404(Challenge, id=challenge_id)
    my_classes = request.user.enrolled_classes.filter(challenges=challenge)

    if not my_classes.exists():
        return HttpResponseForbidden('You are not part of this challenge.')

    quizzes = challenge.quizzes.all()

    # Build quiz status for this student
    quiz_status = []
    for quiz in quizzes:
        submission = StudentQuizSubmission.objects.filter(
            student=request.user, quiz=quiz
        ).first()
        quiz_status.append({
            'quiz': quiz,
            'submitted': submission is not None,
            'score': submission.score if submission else None,
            'total': submission.total if submission else None,
        })

    # Leaderboard
    student_ids = User.objects.filter(
        enrolled_classes__in=challenge.classes.all(), role='student'
    ).distinct().values_list('id', flat=True)

    submissions = StudentQuizSubmission.objects.filter(
        student_id__in=student_ids,
        quiz__in=quizzes,
    ).values('student_id').annotate(
        total_score=models.Sum('score'),
        total_possible=models.Sum('total'),
        quiz_count=models.Count('id'),
    ).order_by('-total_score')

    leaderboard = []
    rank = 1
    for entry in submissions[:20]:
        student = User.objects.get(id=entry['student_id'])
        pct = int((entry['total_score'] / entry['total_possible']) * 100) if entry['total_possible'] > 0 else 0
        leaderboard.append({
            'rank': rank,
            'student': student,
            'score': entry['total_score'],
            'possible': entry['total_possible'],
            'percentage': pct,
            'quizzes': entry['quiz_count'],
            'is_me': student.id == request.user.id,
        })
        rank += 1

    return render(request, 'student_challenge_detail.html', {
        'challenge': challenge,
        'quiz_status': quiz_status,
        'leaderboard': leaderboard,
    })


@login_required
def toggle_instructor_approval_view(request, user_id, approve=True):
    """Approve or disapprove an instructor. Sends email notification."""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden('Not authorized')
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    instructor = get_object_or_404(User, pk=user_id, role='instructor')
    instructor.is_approved = approve
    instructor.save(update_fields=['is_approved'])

    # Send email notification
    try:
        from django.core.mail import send_mail
        subject = 'Account Approved - aris4.0' if approve else 'Account Disapproved - aris4.0'
        message = (
            f"Dear {instructor.username},\n\n"
            f"Your instructor account on aris4.0 has been {'approved' if approve else 'disapproved'}.\n\n"
            f"{'You can now log in and start creating classes.' if approve else 'Please contact the administrator for more information.'}\n\n"
            f"Best regards,\nThe aris4.0 Team"
        )
        send_mail(subject, message, None, [instructor.email], fail_silently=True)
    except Exception:
        pass  # Email failure shouldn't block the approval action

    return JsonResponse({'status': 'approved' if approve else 'disapproved'})


@login_required
def delete_instructor_request_view(request, user_id):
    """Delete a pending instructor registration request."""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden('Not authorized')
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    instructor = get_object_or_404(User, pk=user_id, role='instructor', is_approved=False)
    instructor.delete()
    return JsonResponse({'status': 'deleted'})



# VIEWS: Archive / Library


def archive_view(request, slug=None):
    """Combined archive index + category view."""
    categories = ArchiveCategory.objects.all()
    library_books = LibraryBook.objects.all().order_by('-uploaded_at')

    if slug:
        category = get_object_or_404(ArchiveCategory, slug=slug)
        archive_items = ArchiveItem.objects.filter(category=category).order_by('-id')
        featured_record = ArchiveItem.objects.filter(category=category, is_featured=True).first()
        active_category = slug
    else:
        archive_items = ArchiveItem.objects.all().order_by('-id')
        featured_record = ArchiveItem.objects.filter(is_featured=True).first()
        active_category = None

    context = {
        'categories': categories,
        'archive_items': archive_items,
        'featured_record': featured_record,
        'active_category': active_category,
        'library_books': library_books,
    }
    context.update(get_leaderboard_data(request))
    return render(request, 'archive_repository.html', context)


@login_required
def library_view(request):
    """Show all library books. Instructors can upload new books here."""
    books = LibraryBook.objects.all().order_by('-uploaded_at')

    if request.method == 'POST' and request.user.is_authenticated and request.user.role == 'instructor':
        title = request.POST.get('title', '').strip()
        uploaded_file = request.FILES.get('file')
        if title and uploaded_file:
            LibraryBook.objects.create(
                title=title, description=request.POST.get('description', '').strip(),
                file=uploaded_file, thumbnail=request.FILES.get('thumbnail'),
                uploaded_by=request.user,
            )
            trigger_sync_after_action()  # push new book upstream ASAP
            return redirect('library')

    return render(request, 'library.html', {'books': books})


@login_required
def library_download_view(request, book_id):
    """Download a library book file."""
    from django.http import FileResponse
    book = get_object_or_404(LibraryBook, id=book_id)
    return FileResponse(book.file.open('rb'), as_attachment=True, filename=book.file.name)


@login_required
def library_delete_view(request, book_id):
    """Delete a library book (only the instructor who uploaded it)."""
    if request.user.role != 'instructor':
        return redirect('home')
    book = get_object_or_404(LibraryBook, id=book_id, uploaded_by=request.user)
    if request.method == 'POST':
        book.file.delete(save=False)
        if book.thumbnail:
            book.thumbnail.delete(save=False)
        book.delete()
        trigger_sync_after_action()  # push deletion upstream ASAP
        return redirect('library')
    return redirect('library')



# VIEWS: Quiz System


@login_required
def student_take_quiz_view(request, quiz_id):
    """Student submits answers for a quiz."""
    if request.user.role != 'student':
        return redirect('home')

    quiz = get_object_or_404(Quiz, id=quiz_id)

    existing = StudentQuizSubmission.objects.filter(student=request.user, quiz=quiz).first()
    if existing:
        return redirect('student_quiz_result', quiz_id=quiz_id)

    questions = list(quiz.questions.prefetch_related('choices').all())
    for q in questions:
        q.shuffled_choices = list(q.choices.all())
        random.shuffle(q.shuffled_choices)

    if request.method == 'POST':
        score = 0
        total = len(questions)
        answers = {}
        for question in questions:
            choice_id = request.POST.get(f'question_{question.id}')
            if choice_id:
                selected_choice = get_object_or_404(Choice, id=choice_id, question=question)
                answers[str(question.id)] = int(choice_id)
                if selected_choice.is_correct:
                    score += 1

        StudentQuizSubmission.objects.create(
            student=request.user, quiz=quiz, score=score, total=total, answers=answers,
        )
        request.user.xp = (request.user.xp or 0) + (score * 50)
        request.user.save(update_fields=['xp'])
        trigger_sync_after_action()  # push quiz result upstream ASAP
        return redirect('student_quiz_result', quiz_id=quiz_id)

    return render(request, 'student_take_quiz.html', {'quiz': quiz, 'questions': questions})


@login_required
def student_quiz_result_view(request, quiz_id):
    """Student views their quiz result."""
    if request.user.role != 'student':
        return redirect('home')

    quiz = get_object_or_404(Quiz, id=quiz_id)
    submission = get_object_or_404(StudentQuizSubmission, student=request.user, quiz=quiz)
    questions = quiz.questions.prefetch_related('choices').all()

    return render(request, 'student_quiz_result.html', {
        'quiz': quiz,
        'submission': submission,
        'results': build_question_results(submission, questions),
    })


@login_required
def instructor_quiz_submissions_view(request, quiz_id):
    """Instructor views all student submissions for a quiz (compact list)."""
    if request.user.role != 'instructor':
        return redirect('home')

    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.academic_class and quiz.academic_class.instructor != request.user:
        return redirect('home')

    submissions = StudentQuizSubmission.objects.filter(quiz=quiz).select_related('student').order_by('-score')
    enrolled_students = quiz.academic_class.students.all() if quiz.academic_class else []
    submitted_ids = {s.student_id for s in submissions}
    pending_students = [s for s in enrolled_students if s.id not in submitted_ids]

    total_score_sum = sum(s.score for s in submissions)
    avg_score = round(total_score_sum / submissions.count(), 1) if submissions.count() > 0 else 0

    return render(request, 'instructor_quiz_submissions.html', {
        'quiz': quiz, 'submissions': submissions, 'pending_students': pending_students,
        'total_submissions': submissions.count(),
        'total_enrolled': enrolled_students.count(), 'avg_score': avg_score,
    })


@login_required
def instructor_quiz_submission_detail_view(request, quiz_id, student_id):
    """Instructor views a single student's submission with full question breakdown."""
    if request.user.role != 'instructor':
        return redirect('home')

    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.academic_class and quiz.academic_class.instructor != request.user:
        return redirect('home')

    student = get_object_or_404(User, id=student_id, role='student')
    submission = get_object_or_404(StudentQuizSubmission, quiz=quiz, student=student)
    questions = list(quiz.questions.prefetch_related('choices').all())
    question_results = build_question_results(submission, questions)

    # Build navigation: sorted list of students who submitted
    all_subs = StudentQuizSubmission.objects.filter(quiz=quiz).select_related('student').order_by('-score')
    sub_list = list(all_subs)
    prev_sub = None
    next_sub = None
    for i, s in enumerate(sub_list):
        if s.student_id == student.id:
            if i > 0:
                prev_sub = sub_list[i - 1]
            if i < len(sub_list) - 1:
                next_sub = sub_list[i + 1]
            break

    return render(request, 'instructor_quiz_submission_detail.html', {
        'quiz': quiz, 'student': student, 'submission': submission,
        'question_results': question_results,
        'prev_sub': prev_sub, 'next_sub': next_sub,
        'submission_index': next((i for i, s in enumerate(sub_list) if s.student_id == student.id), 0) + 1,
        'total_submissions': len(sub_list),
    })


@login_required
def instructor_student_performance_view(request, slug, student_id):
    """Instructor views a specific student's performance across all quizzes in a class."""
    if request.user.role != 'instructor':
        return redirect('home')

    academic_class = get_object_or_404(AcademicClass, slug=slug, instructor=request.user)
    student = get_object_or_404(User, id=student_id, role='student')

    if student not in academic_class.students.all():
        return redirect('instructor_class', slug=slug)

    quizzes = academic_class.quizzes.prefetch_related('questions__choices').all()
    submissions = StudentQuizSubmission.objects.filter(student=student, quiz__in=quizzes).select_related('quiz')
    submission_map = {s.quiz_id: s for s in submissions}

    quiz_results = [
        {
            'quiz': quiz,
            'submission': submission_map.get(quiz.id),
            'has_submitted': submission_map.get(quiz.id) is not None,
            'question_details': build_question_results(submission_map[quiz.id], quiz.questions.all())
            if quiz.id in submission_map else [],
        }
        for quiz in quizzes
    ]

    # Build sorted student list for navigation
    all_quizzes = list(academic_class.quizzes.all())
    all_submissions = StudentQuizSubmission.objects.filter(quiz__in=all_quizzes).select_related('student')
    nav_stats = {}
    for s in academic_class.students.all():
        nav_stats[s.id] = {'completed_quizzes': 0, 'total_score': 0}
    for sub in all_submissions:
        if sub.student_id in nav_stats:
            nav_stats[sub.student_id]['completed_quizzes'] += 1
            nav_stats[sub.student_id]['total_score'] += sub.score
    sorted_students = sorted(
        academic_class.students.all(),
        key=lambda s: (s.get_full_name() or s.username).lower()
    )

    prev_student = None
    next_student = None
    for i, s in enumerate(sorted_students):
        if s.id == student.id:
            if i > 0:
                prev_student = sorted_students[i - 1]
            if i < len(sorted_students) - 1:
                next_student = sorted_students[i + 1]
            break

    return render(request, 'instructor_student_performance.html', {
        'class': academic_class, 'student': student, 'quiz_results': quiz_results,
        'total_quizzes': quizzes.count(), 'completed_quizzes': submissions.count(),
        'total_score': sum(s.score for s in submissions),
        'total_possible': sum(s.total for s in submissions),
        'prev_student': prev_student,
        'next_student': next_student,
        'all_students': sorted_students,
    })


# ================================================================
# NOTIFICATIONS
# ================================================================

@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user)[:30]
    unread = notifs.filter(is_read=False)
    # Mark displayed as read
    unread.update(is_read=True)
    return render(request, 'notifications.html', {'notifications': notifs})


# ================================================================
# PARENT PORTAL  (existing views above)
# ================================================================
    return render(request, 'parent_link_child.html')
