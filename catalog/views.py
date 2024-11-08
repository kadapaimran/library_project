from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from .models import Book, Borrowing


def home(request):
    if request.user.is_authenticated:
        return redirect('book_list')
    return render(request, 'catalog/home.html')


@login_required
def book_list(request):
    query = request.GET.get('q', '')
    books = Book.objects.all()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(genre__icontains=query)
        )

    return render(request, 'catalog/book_list.html', {
        'books': books,
        'query': query,
        'now': timezone.now()
    })


@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, 'catalog/book_detail.html', {
        'book': book,
        'now': timezone.now()
    })


@login_required
def borrow_book(request, pk):
    if request.method == 'POST':
        book = get_object_or_404(Book, pk=pk)
        if book.is_available():
            due_date = timezone.now() + timezone.timedelta(days=14)
            Borrowing.objects.create(
                user=request.user,
                book=book,
                due_date=due_date
            )
            messages.success(request, f'You have successfully borrowed "{book.title}"')
        else:
            messages.error(request, 'This book is currently not available')
    return redirect('book_detail', pk=pk)