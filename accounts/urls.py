from django.urls import path
from . import views

urlpatterns = [
    # Core Base Views
    path('', views.home_view, name="home"),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('select-level/', views.select_level_view, name='select_level'),
    path('pending-approval/', views.pending_approval_view, name='pending_approval'),
    path('kamati/<int:id>/', views.kamati_view, name='kamati'),
    path('dashboard/', views.instructor_dashboard_view, name='dashboard'),
    path('instructor-dashboard/', views.instructor_dashboard_view, name='instructor_dashboard'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('teacher-profile/', views.teacher_profile_view, name='teacher_profile'),
    path('student-profile/', views.student_profile_view, name='student_profile'),
    path('quiz/<int:quiz_id>/', views.quiz_detail_view, name='quiz_detail'),
    path('submit-assignment/<int:item_id>/', views.submit_assignment_view, name='submit_assignment'),
    path('submit-quiz-response/<int:quiz_id>/', views.submit_quiz_response_view, name='submit_quiz_response'),
    path('apply-mentorship/', views.apply_mentorship_view, name='apply_mentorship'),
    path('dossier-archive/', views.dossier_archive_view, name='dossier_archive'),
    path('admin-dashboard/approve/<int:user_id>/', views.approve_instructor_view, name='approve_instructor'),
    path('admin-dashboard/disapprove/<int:user_id>/', views.disapprove_instructor_view, name='disapprove_instructor'),
    path('test/', views.tail, name='test'),
    
    # Student Dashboard Routing Group
    path('study/', views.student_dashboard_view, name='study_dashboard'),
    path('study/deadlines/', views.deadlines_list_view, name='deadlines_list'),
    path('study/class/<slug:slug>/', views.class_detail_view, name='class_detail'),
    
    # Digital Repository Archive Routing Group
    path('archive/', views.archive_index_view, name='archive_index'),
    path('archive/category/<slug:slug>/', views.archive_category_view, name='archive_category'),
]