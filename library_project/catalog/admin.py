from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Book, Borrowing

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'total_copies', 'available_copies')
    search_fields = ('title', 'author', 'isbn')
    list_filter = ('genre', 'available_copies')

@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'borrowed_date', 'due_date', 'returned_date')
    search_fields = ('user__username', 'book__title')
    list_filter = ('returned_date', 'due_date')