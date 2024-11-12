from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.librarian_dashboard, name='librarian_dashboard'),
    path('book/add/', views.add_book, name='add_book'),
    path('book/<int:pk>/edit/', views.edit_book, name='edit_book'),
    path('book/<int:pk>/delete/', views.delete_book, name='delete_book'),
    path('borrowing/<int:pk>/return/', views.return_book, name='return_book'),
    path('reports/', views.borrowing_reports, name='borrowing_reports'),
]