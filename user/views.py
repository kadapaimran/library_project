from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from catalog.models import Borrowing, Book
from .forms import SignUpForm


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Check if username starts with 'LIB' to assign librarian status
            if user.username.upper().startswith('LIB'):
                user.is_staff = True
                user.save()

            login(request, user)
            messages.success(request, 'Account created successfully!')

            if user.is_staff:
                return redirect('librarian_dashboard')
            return redirect('book_list')
    else:
        form = SignUpForm()
    return render(request, 'user/signup.html', {'form': form})


@login_required
def user_dashboard(request):
    if request.user.is_staff:
        return redirect('librarian_dashboard')

    active_borrowings = Borrowing.objects.filter(
        user=request.user,
        returned_date__isnull=True
    ).select_related('book')

    for borrowing in active_borrowings:
        borrowing.is_overdue = borrowing.due_date < timezone.now()

    return render(request, 'user/dashboard.html', {
        'active_borrowings': active_borrowings,
        'now': timezone.now()
    })


@login_required
def user_profile(request):
    return render(request, 'user/profile.html', {
        'user': request.user
    })


@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('user_profile')

    return render(request, 'user/edit_profile.html', {
        'user': request.user
    })


@login_required
def borrowing_history(request):
    borrowings = Borrowing.objects.filter(
        user=request.user
    ).select_related('book').order_by('-borrowed_date')

    return render(request, 'user/borrowing_history.html', {
        'borrowings': borrowings,
        'now': timezone.now()
    })


@login_required
def download_book(request, pk):
    borrowing = get_object_or_404(Borrowing, pk=pk, user=request.user)
    if borrowing.returned_date is None:
        return redirect(borrowing.book.pdf_file.url)
    messages.error(request, 'You can no longer access this book as it has been returned.')
    return redirect('user_dashboard')


from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages



@login_required
def update_progress(request, borrowing_id):
    borrowing = get_object_or_404(Borrowing, pk=borrowing_id, user=request.user)

    if request.method == 'POST':
        progress = request.POST.get('progress')
        try:
            progress = int(progress)
            if 0 <= progress <= 100:
                borrowing.progress = progress
                borrowing.save()
                messages.success(request, 'Reading progress updated successfully!')
            else:
                messages.error(request, 'Progress must be between 0 and 100.')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid progress value.')

    return redirect('user_dashboard')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from catalog.models import Borrowing, Book
from .forms import SignUpForm


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Check if username starts with 'LIB' to assign librarian status
            if user.username.upper().startswith('LIB'):
                user.is_staff = True
                user.save()

            # Send welcome email
            send_mail(
                'Welcome to the Library',
                f'Dear {user.username}!,\n\nWelcome to our library system! Your account has been created successfully.\n\nBest regards,\nLibrary Team',
                 'kadapaimran99@gmail.com',
                [user.email],
                fail_silently=False,
            )

            login(request, user)
            messages.success(request, 'Account created successfully! Welcome email sent.')

            if user.is_staff:
                return redirect('librarian_dashboard')
            return redirect('book_list')
    else:
        form = SignUpForm()
    return render(request, 'user/signup.html', {'form': form})


@login_required
def return_book(request, pk):
    borrowing = get_object_or_404(Borrowing, pk=pk, user=request.user)
    if request.method == 'POST':
        borrowing.returned_date = timezone.now()
        borrowing.save()
        borrowing.book.available_copies += 1
        borrowing.book.save()
        messages.success(request, f'You have successfully returned "{borrowing.book.title}"')
    return redirect('user_dashboard')

@login_required
def update_progress(request, borrowing_id):
    borrowing = get_object_or_404(Borrowing, pk=borrowing_id, user=request.user)

    if request.method == 'POST':
        progress = request.POST.get('progress')
        try:
            progress = int(progress)
            if 0 <= progress <= 100:
                borrowing.progress = progress
                borrowing.save()
                messages.success(request, 'Reading progress updated successfully!')
            else:
                messages.error(request, 'Progress must be between 0 and 100.')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid progress value.')

    return redirect('user_dashboard')

