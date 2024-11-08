from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from catalog.models import Borrowing
from datetime import timedelta

class Command(BaseCommand):
    help = 'Send reminder emails for books due in 2 days'

    def handle(self, *args, **kwargs):
        two_days_from_now = timezone.now() + timedelta(days=2)
        due_borrowings = Borrowing.objects.filter(
            returned_date__isnull=True,
            reminder_sent=False,
            due_date__date=two_days_from_now.date()
        ).select_related('user', 'book')

        for borrowing in due_borrowings:
            send_mail(
                'Book Return Reminder',
                f'Dear {borrowing.user.username},\n\n'
                f'This is a reminder that the book "{borrowing.book.title}" is due to be returned '
                f'on {borrowing.due_date.strftime("%B %d, %Y")}.\n\n'
                'Please ensure to return it on time to avoid any late fees.\n\n'
                'Best regards,\nLibrary Team',
                settings.DEFAULT_FROM_EMAIL,
                [borrowing.user.email],
                fail_silently=False,
            )
            borrowing.reminder_sent = True
            borrowing.save()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {due_borrowings.count()} reminder emails')
        )