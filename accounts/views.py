from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm
from .models import User


def home_view(request):
    return render(request, 'accounts/home.html')


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
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.role == 'student':
                return redirect('select_level')
            elif user.role == 'instructor':
                return redirect('pending_approval')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def select_level_view(request):
    return render(request, 'accounts/select_level.html')

def pending_approval_view(request):
    return render(request, 'accounts/pending_approval.html')