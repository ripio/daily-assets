from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from core.forms import UserCreateForm, UserEditForm
from core.models import UserProfile


def _require_admin(request):
    if not request.user.is_authenticated:
        return False
    profile = getattr(request.user, 'profile', None)
    return profile and profile.is_admin()


@login_required
def list_users(request):
    if not _require_admin(request):
        messages.error(request, 'Acceso restringido a administradores.')
        return redirect('dashboard')
    users = User.objects.select_related('profile').order_by('username')
    return render(request, 'users/list.html', {'users': users})


@login_required
def create_user(request):
    if not _require_admin(request):
        messages.error(request, 'Acceso restringido a administradores.')
        return redirect('dashboard')
    form = UserCreateForm()
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            user = User.objects.create_user(
                username=d['username'],
                email=d['email'],
                password=d['password'],
                first_name=d.get('first_name', ''),
                last_name=d.get('last_name', ''),
            )
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = d['role']
            profile.save()
            messages.success(request, f'Usuario {user.username} creado correctamente.')
            return redirect('users_list')
    return render(request, 'users/create.html', {'form': form})


@login_required
def edit_user(request, pk):
    if not _require_admin(request):
        messages.error(request, 'Acceso restringido a administradores.')
        return redirect('dashboard')
    target = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=target)
    initial = {
        'email': target.email,
        'first_name': target.first_name,
        'last_name': target.last_name,
        'role': profile.role,
    }
    form = UserEditForm(initial=initial)
    if request.method == 'POST':
        form = UserEditForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            target.email = d['email']
            target.first_name = d.get('first_name', '')
            target.last_name = d.get('last_name', '')
            target.save()
            profile.role = d['role']
            profile.save()
            if d.get('new_password'):
                target.set_password(d['new_password'])
                target.save()
            messages.success(request, f'Usuario {target.username} actualizado.')
            return redirect('users_list')
    return render(request, 'users/edit.html', {'form': form, 'target': target})


@login_required
def toggle_user(request, pk):
    if not _require_admin(request):
        messages.error(request, 'Acceso restringido a administradores.')
        return redirect('dashboard')
    target = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if target == request.user:
            messages.error(request, 'No podés desactivar tu propia cuenta.')
            return redirect('users_list')
        target.is_active = not target.is_active
        target.save()
        estado = 'activado' if target.is_active else 'desactivado'
        messages.success(request, f'Usuario {target.username} {estado}.')
    return redirect('users_list')
