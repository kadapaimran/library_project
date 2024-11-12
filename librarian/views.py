from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth.models import User
from datetime import timedelta
from catalog.models import Book, Borrowing

def is_librarian(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_librarian)
def librarian_dashboard(request):
    search_query = request.GET.get('search', '')
    user_search = request.GET.get('user_search', '')

    books = Book.objects.all().order_by('-created_at')
    borrowings = Borrowing.objects.filter(
        returned_date__isnull=True
    ).select_related('user', 'book').order_by('due_date')

    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query)
        )

    user_details = None
    if user_search:
        try:
            user_details = User.objects.get(
                Q(username__icontains=user_search) |
                Q(email__icontains=user_search)
            )
            user_details.borrowing_history = Borrowing.objects.filter(
                user=user_details
            ).select_related('book').order_by('-borrowed_date')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')

    return render(request, 'librarian/dashboard.html', {
        'books': books,
        'borrowings': borrowings,
        'search_query': search_query,
        'user_search': user_search,
        'user_details': user_details,
        'now': timezone.now()
    })

@user_passes_test(is_librarian)
def add_book(request):
    if request.method == 'POST':
        book = Book.objects.create(
            title=request.POST['title'],
            author=request.POST['author'],
            isbn=request.POST['isbn'],
            genre=request.POST['genre'],
            description=request.POST['description'],
            cover_image=request.FILES.get('cover_image'),
            pdf_file=request.FILES['pdf_file'],
            total_copies=int(request.POST.get('total_copies', 1)),
            available_copies=int(request.POST.get('total_copies', 1))
        )
        messages.success(request, 'Book added successfully!')
        return redirect('librarian_dashboard')
    return render(request, 'librarian/add_book.html')

@user_passes_test(is_librarian)
def edit_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.title = request.POST['title']
        book.author = request.POST['author']
        book.isbn = request.POST['isbn']
        book.genre = request.POST['genre']
        book.description = request.POST['description']
        
        new_total_copies = int(request.POST.get('total_copies', book.total_copies))
        copies_difference = new_total_copies - book.total_copies
        book.total_copies = new_total_copies
        book.available_copies = max(0, book.available_copies + copies_difference)

        if 'cover_image' in request.FILES:
            book.cover_image = request.FILES['cover_image']
        if 'pdf_file' in request.FILES:
            book.pdf_file = request.FILES['pdf_file']
        
        book.save()
        messages.success(request, 'Book updated successfully!')
        return redirect('librarian_dashboard')
    
    return render(request, 'librarian/edit_book.html', {'book': book})

@user_passes_test(is_librarian)
def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    # Check if book has any active borrowings
    active_borrowings = Borrowing.objects.filter(
        book=book,
        returned_date__isnull=True
    ).exists()
    
    if active_borrowings:
        messages.error(request, 'Cannot delete book while it has active borrowings.')
        return redirect('librarian_dashboard')
    
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Book deleted successfully!')
        return redirect('librarian_dashboard')
    
    return render(request, 'librarian/delete_book.html', {'book': book})

@user_passes_test(is_librarian)
def return_book(request, pk):
    borrowing = get_object_or_404(Borrowing, pk=pk)
    if request.method == 'POST':
        borrowing.returned_date = timezone.now()
        borrowing.save()
        borrowing.book.available_copies += 1
        borrowing.book.save()
        messages.success(request, 'Book marked as returned successfully!')
    return redirect('librarian_dashboard')

@user_passes_test(is_librarian)
def borrowing_reports(request):
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    total_books = Book.objects.count()
    total_borrowings = Borrowing.objects.filter(
        borrowed_date__gte=start_date
    ).count()
    active_borrowings = Borrowing.objects.filter(
        returned_date__isnull=True
    ).count()
    overdue_borrowings = Borrowing.objects.filter(
        returned_date__isnull=True,
        due_date__lt=timezone.now()
    ).count()
    
    popular_books = Book.objects.annotate(
        borrow_count=Count('borrowing', filter=Q(borrowing__borrowed_date__gte=start_date))
    ).order_by('-borrow_count')[:5]
    
    genre_distribution = Borrowing.objects.filter(
        borrowed_date__gte=start_date
    ).values('book__genre').annotate(
        count=Count('id')
    ).order_by('-count')
    
    recent_borrowings = Borrowing.objects.filter(
        borrowed_date__gte=start_date
    ).select_related('user', 'book').order_by('-borrowed_date')[:10]
    
    context = {
        'days': days,
        'total_books': total_books,
        'total_borrowings': total_borrowings,
        'active_borrowings': active_borrowings,
        'overdue_borrowings': overdue_borrowings,
        'popular_books': popular_books,
        'genre_distribution': genre_distribution,
        'recent_borrowings': recent_borrowings,
        'now': timezone.now()
    }
    
    return render(request, 'librarian/reports.html', context)