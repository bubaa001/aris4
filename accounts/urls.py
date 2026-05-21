
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name="home"),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('select-level/', views.select_level_view, name='select_level'),
    path('pending-approval/', views.pending_approval_view, name='pending_approval'),
]
