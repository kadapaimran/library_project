from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import FileResponse, JsonResponse
from catalog.models import Borrowing, Book
from .forms import SignUpForm


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()

                    # Check if username starts with 'LIB' to assign librarian status
                    if user.username.upper().startswith('LIB'):
                        user.is_staff = True
                        user.save()

                    # Send welcome email
                    send_mail(
                        'Welcome to the Library',
                        f'''Dear {user.username},

Welcome to our library system! Your account has been created successfully.

You can now:
- Browse our extensive collection of books
- Borrow books online
- Track your reading progress
- Receive notifications about due dates

Happy reading!

Best regards,
Library Team''',
                        'kadapaimran99@gmail.com',
                        [user.email],
                        fail_silently=True,
                    )

                    login(request, user)
                    messages.success(request, 'Account created successfully! Welcome to our library.')

                    if user.is_staff:
                        return redirect('librarian_dashboard')
                    return redirect('book_list')
            except Exception as e:
                messages.error(request, f'An error occurred during signup: {str(e)}')
                return redirect('signup')
    else:
        form = SignUpForm()
    return render(request, 'user/signup.html', {'form': form})


@login_required
def user_dashboard(request):
    # Get active borrowings
    active_borrowings = Borrowing.objects.filter(
        user=request.user,
        returned_date__isnull=True
    ).select_related('book').order_by('due_date')

    # Calculate overdue status and reading progress
    for borrowing in active_borrowings:
        borrowing.is_overdue = borrowing.due_date < timezone.now()
        if hasattr(borrowing, 'current_page'):
            total_pages = borrowing.book.total_pages or 100  # Default to 100 if not set
            borrowing.progress = (borrowing.current_page / total_pages) * 100
        else:
            borrowing.progress = 0

    # Get reading statistics
    total_books_read = Borrowing.objects.filter(
        user=request.user,
        returned_date__isnull=False
    ).count()

    currently_reading = active_borrowings.count()

    context = {
        'active_borrowings': active_borrowings,
        'total_books_read': total_books_read,
        'currently_reading': currently_reading,
        'now': timezone.now()
    }

    return render(request, 'user/dashboard.html', context)


@login_required
def user_profile(request):
    # Get user's reading statistics
    total_borrowed = Borrowing.objects.filter(user=request.user).count()
    total_returned = Borrowing.objects.filter(
        user=request.user,
        returned_date__isnull=False
    ).count()
    currently_borrowed = Borrowing.objects.filter(
        user=request.user,
        returned_date__isnull=True
    ).count()

    context = {
        'total_borrowed': total_borrowed,
        'total_returned': total_returned,
        'currently_borrowed': currently_borrowed
    }

    return render(request, 'user/profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user

        # Update user information
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        # Validate email
        if email and email != user.email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, 'This email is already in use.')
                return redirect('edit_profile')
            user.email = email

        try:
            user.save()
            messages.success(request, 'Profile updated successfully!')

            # Send confirmation email
            send_mail(
                'Profile Updated',
                f'''Dear {user.username},

Your profile has been successfully updated.

New Details:
- Name: {user.get_full_name()}
- Email: {user.email}

If you didn't make these changes, please contact us immediately.

Best regards,
Library Team''',
                'kadapaimran99@gmail.com',
                [user.email],
                fail_silently=True,
            )

            return redirect('user_profile')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
            return redirect('edit_profile')

    return render(request, 'user/edit_profile.html')


@login_required
def borrowing_history(request):
    # Get all borrowings with book information
    borrowings = Borrowing.objects.filter(
        user=request.user
    ).select_related('book').order_by('-borrowed_date')

    # Calculate reading duration for returned books
    for borrowing in borrowings:
        if borrowing.returned_date:
            duration = borrowing.returned_date - borrowing.borrowed_date
            borrowing.reading_duration = duration.days
        else:
            duration = timezone.now() - borrowing.borrowed_date
            borrowing.reading_duration = duration.days

    context = {
        'borrowings': borrowings,
        'now': timezone.now()
    }

    return render(request, 'user/borrowing_history.html', context)


@login_required
def download_book(request, pk):
    borrowing = get_object_or_404(Borrowing, pk=pk, user=request.user)

    # Check if the book is still borrowed
    if borrowing.returned_date:
        messages.error(request, 'You cannot download a book that has been returned.')
        return redirect('user_dashboard')

    try:
        # Log the download
        borrowing.last_accessed = timezone.now()
        borrowing.save()

        # Serve the PDF file
        response = FileResponse(
            borrowing.book.pdf_file,
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{borrowing.book.title}.pdf"'
        return response
    except Exception as e:
        messages.error(request, 'Error downloading the book. Please try again later.')
        return redirect('user_dashboard')


@login_required
def return_book(request, pk):
    borrowing = get_object_or_404(Borrowing, pk=pk, user=request.user)

    if not borrowing.returned_date:
        try:
            with transaction.atomic():
                # Mark as returned
                borrowing.returned_date = timezone.now()
                borrowing.save()

                # Update book availability
                borrowing.book.available_copies += 1
                borrowing.book.save()

                # Send return confirmation email
                send_mail(
                    'Book Return Confirmation',
                    f'''Dear {request.user.username},

Thank you for returning "{borrowing.book.title}".

Return Details:
- Book: {borrowing.book.title}
- Return Date: {borrowing.returned_date.strftime('%B %d, %Y')}
- Reading Duration: {(borrowing.returned_date - borrowing.borrowed_date).days} days

We hope you enjoyed reading it!

Best regards,
Library Team''',
                    'kadapaimran99@gmail.com',
                    [request.user.email],
                    fail_silently=True,
                )

                messages.success(request, f'"{borrowing.book.title}" has been returned successfully.')
        except Exception as e:
            messages.error(request, f'Error returning book: {str(e)}')

    return redirect('user_dashboard')


@login_required
def update_progress(request):
    if request.method == 'POST':
        borrowing_id = request.POST.get('borrowing_id')
        page_number = request.POST.get('page_number')

        try:
            # Get active borrowing
            borrowing = Borrowing.objects.get(
                id=borrowing_id,
                user=request.user,
                returned_date__isnull=True
            )

            # Update progress
            page_number = int(page_number)
            total_pages = borrowing.book.total_pages or 100

            if 0 <= page_number <= total_pages:
                borrowing.current_page = page_number
                borrowing.last_accessed = timezone.now()
                borrowing.save()

                # Calculate progress percentage
                progress = (page_number / total_pages) * 100

                return JsonResponse({
                    'status': 'success',
                    'progress': progress,
                    'page': page_number,
                    'total_pages': total_pages
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid page number'
                })

        except (Borrowing.DoesNotExist, ValueError, TypeError):
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid request'
            })

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })