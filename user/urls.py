from django.urls import path
from django.contrib.auth import views as auth_views
from . import views



urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='user/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('borrowing-history/', views.borrowing_history, name='borrowing_history'),
    path('download-book/<int:pk>/', views.download_book, name='download_book'),
    path('return-book/<int:pk>/', views.return_book, name='return_book'),
    path('borrowing/2/update-progress/',views.update_progress, name='update_progress'),
]