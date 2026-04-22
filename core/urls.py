from django.urls import path
from core.views import auth_views, dashboard, balance, upload, users

urlpatterns = [
    # Auth
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('mi-cuenta/', auth_views.change_password_view, name='change_password'),

    # Dashboard (charts)
    path('', dashboard.index, name='dashboard'),

    # Balance Ripio (table)
    path('balance/', balance.index, name='balance'),

    # Upload
    path('upload/', upload.index, name='upload'),
    path('upload/delete/<int:pk>/', upload.delete_upload, name='delete_upload'),
    path('upload/confirm/<int:pk>/', upload.confirm_replace, name='confirm_replace'),

    # User management (admin only)
    path('users/', users.list_users, name='users_list'),
    path('users/create/', users.create_user, name='users_create'),
    path('users/<int:pk>/edit/', users.edit_user, name='users_edit'),
    path('users/<int:pk>/toggle/', users.toggle_user, name='users_toggle'),
]
