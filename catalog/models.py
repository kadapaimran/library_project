from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
from collections import Counter

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, unique=True)
    genre = models.CharField(max_length=100)
    description = models.TextField()
    cover_image = models.ImageField(upload_to='covers/', null=True, blank=True)
    pdf_file = models.FileField(upload_to='books/')
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Book'
        verbose_name_plural = 'Books'

    def __str__(self):
        return self.title

    def generate_due_date(self):
        days = random.randint(14, 30)
        return timezone.now() + timedelta(days=days)

    def is_available(self):
        return self.available_copies > 0

    @classmethod
    def get_recommendations(cls, user, limit=5):
        # Get user's reading history
        user_borrowings = Borrowing.objects.filter(user=user).select_related('book')
        
        if not user_borrowings.exists():
            # If no history, return popular books
            return cls.objects.filter(available_copies__gt=0).order_by('-id')[:limit]
        
        # Get genres and authors from user's history
        genres = Counter(b.book.genre for b in user_borrowings)
        authors = Counter(b.book.author for b in user_borrowings)
        
        # Find books with similar genres and authors
        favorite_genres = [genre for genre, _ in genres.most_common(3)]
        favorite_authors = [author for author, _ in authors.most_common(3)]
        
        # Exclude books already borrowed
        borrowed_books = set(b.book.id for b in user_borrowings)
        
        recommendations = cls.objects.filter(
            models.Q(genre__in=favorite_genres) |
            models.Q(author__in=favorite_authors),
            available_copies__gt=0
        ).exclude(
            id__in=borrowed_books
        ).distinct()
        
        return recommendations[:limit]

class Borrowing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrowed_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    returned_date = models.DateTimeField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Borrowing'
        verbose_name_plural = 'Borrowings'

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = self.book.generate_due_date()
        if not self.pk and not self.returned_date:  # New borrowing
            self.book.available_copies -= 1
            self.book.save()
        super().save(*args, **kwargs)

    @classmethod
    def user_can_borrow(cls, user, book):
        """Check if user can borrow this specific book"""
        # Check if user already has this book
        has_book = cls.objects.filter(
            user=user,
            book=book,
            returned_date__isnull=True
        ).exists()
        
        if has_book:
            return False, "You already have this book borrowed"
        
        return True, None