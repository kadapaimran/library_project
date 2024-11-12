from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Book, Borrowing


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'genre', 'availability_status', 'cover_preview')
    list_filter = ('genre', 'available_copies')
    search_fields = ('title', 'author', 'isbn')
    readonly_fields = ('cover_preview',)
    fieldsets = (
        ('Book Information', {
            'fields': ('title', 'author', 'isbn', 'genre', 'description')
        }),
        ('Availability', {
            'fields': ('total_copies', 'available_copies')
        }),
        ('Media', {
            'fields': ('cover_image', 'cover_preview', 'pdf_file')
        }),
    )

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.cover_image.url)
        return "No cover image"

    cover_preview.short_description = 'Cover Preview'

    def availability_status(self, obj):
        if obj.available_copies > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{} available</span>',
                obj.available_copies
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">Not available</span>'
        )

    availability_status.short_description = 'Availability'


@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'borrowed_date', 'due_date', 'status', 'reading_progress')
    list_filter = ('returned_date', 'due_date', 'reminder_sent')
    search_fields = ('user__username', 'book__title')
    date_hierarchy = 'borrowed_date'

    def status(self, obj):
        if obj.returned_date:
            return format_html(
                '<span style="color: green;">Returned on {}</span>',
                obj.returned_date.strftime('%Y-%m-%d')
            )
        elif obj.due_date < timezone.now():
            return format_html(
                '<span style="color: red; font-weight: bold;">Overdue</span>'
            )
        return format_html(
            '<span style="color: blue;">Active</span>'
        )

    def reading_progress(self, obj):
        if hasattr(obj, 'current_page') and obj.current_page:
            total_pages = obj.book.total_pages or 100
            progress = (obj.current_page / total_pages) * 100
            return format_html(
                '<div style="width: 100px; background: #eee;">'
                '<div style="width: {}%; background: #007bff; height: 20px; text-align: center; color: white;">'
                '{:.0f}%</div></div>',
                min(progress, 100), progress
            )
        return "No progress recorded"