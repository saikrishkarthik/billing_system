from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_invoice_email(email, invoice_details):
    send_mail(
        "Invoice Details",
        invoice_details,
        "yourshop@example.com",
        [email],
        fail_silently=False,
    )
