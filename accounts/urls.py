from django.urls import path
from . import views

urlpatterns = [
    # Core Base Views
    path('', views.home_view, name="home"),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('select-level/', views.select_level_view, name='select_level'),
    path('pending-approval/', views.pending_approval_view, name='pending_approval'),
    path('instructor-dashboard/', views.instructor_dashboard_view, name='instructor_dashboard'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('teacher-profile/', views.teacher_profile_view, name='teacher_profile'),
    path('teacher-profile/edit/', views.edit_instructor_profile_view, name='edit_instructor_profile'),
    path('teacher-profile/<str:username>/', views.teacher_profile_view, name='teacher_profile_by_username'),
    path('instructor/manage-classes/', views.instructor_manage_classes_view, name='instructor_manage_classes'),
    path('student-profile/', views.student_profile_view, name='student_profile'),
    path('student-profile/edit/', views.edit_student_profile_view, name='edit_student_profile'),
    path('student-profile/<str:username>/', views.student_profile_view, name='student_profile_by_username'),
    path('admin-dashboard/approve/<int:user_id>/', views.toggle_instructor_approval_view, {'approve': True}, name='approve_instructor'),
    path('admin-dashboard/disapprove/<int:user_id>/', views.toggle_instructor_approval_view, {'approve': False}, name='disapprove_instructor'),
    path('admin-dashboard/delete/<int:user_id>/', views.delete_instructor_request_view, name='delete_instructor_request'),
    path('admin-dashboard/reset-xp/', views.admin_reset_xp_view, name='admin_reset_xp'),
    path('admin-dashboard/challenge/create/', views.admin_challenge_create_view, name='admin_challenge_create'),
    path('admin-dashboard/challenge/<int:challenge_id>/toggle/', views.admin_challenge_toggle_view, name='admin_challenge_toggle'),
    path('admin-dashboard/challenge/<int:challenge_id>/award/', views.admin_challenge_award_view, name='admin_challenge_award'),
    path('admin-dashboard/instructor/<int:instructor_id>/', views.admin_instructor_progress_view, name='admin_instructor_progress'),
    path('challenge/<int:challenge_id>/leaderboard/', views.challenge_leaderboard_view, name='challenge_leaderboard'),
    path('logout/', views.logout_view, name='logout'),
    
    # Student Dashboard Routing Group
    path('study/', views.student_dashboard_view, name='study_dashboard'),
    path('study/class/<slug:slug>/', views.student_class_view, name='student_class'),
    
    # Instructor Class Management
    path('instructor/class/<slug:slug>/', views.instructor_class_view, name='instructor_class'),
    path('instructor/class/<slug:slug>/students/', views.instructor_student_directory_view, name='instructor_student_directory'),
    
    # Digital Repository Archive Routing Group
    path('archive/', views.archive_view, name='archive_index'),
    path('archive/category/<slug:slug>/', views.archive_view, name='archive_category'),
    path('archive/library/', views.library_view, name='library'),
    path('archive/library/<int:book_id>/download/', views.library_download_view, name='library_download'),
    path('archive/library/<int:book_id>/delete/', views.library_delete_view, name='library_delete'),

    # Student Quiz System
    path('quiz/<int:quiz_id>/take/', views.student_take_quiz_view, name='student_take_quiz'),
    path('quiz/<int:quiz_id>/result/', views.student_quiz_result_view, name='student_quiz_result'),
    
    # Instructor Quiz Submissions
    path('instructor/quiz/<int:quiz_id>/submissions/', views.instructor_quiz_submissions_view, name='instructor_quiz_submissions'),
    path('instructor/quiz/<int:quiz_id>/submissions/<int:student_id>/', views.instructor_quiz_submission_detail_view, name='instructor_quiz_submission_detail'),
    
    # Instructor Student Performance (across all quizzes in a class)
    path('instructor/class/<slug:slug>/student/<int:student_id>/', views.instructor_student_performance_view, name='instructor_student_performance'),
    
    # Parent Portal
    path('parent/register/<str:link_code>/', views.parent_register_view, name='parent_register'),
    path('parent/dashboard/', views.parent_dashboard_view, name='parent_dashboard'),
    path('parent/child/<int:student_id>/', views.parent_child_detail_view, name='parent_child_detail'),
    path('parent/child/<int:student_id>/quiz/<int:quiz_id>/', views.parent_child_quiz_result_view, name='parent_child_quiz_result'),
]
