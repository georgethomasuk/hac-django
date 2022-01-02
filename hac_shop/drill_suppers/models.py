import uuid
from datetime import datetime, timedelta, timezone

import stripe
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import fields
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

SERVER_URL = "http://localhost:8000"


class AfterDrillNightCutOffError(Exception):
    pass


class OnSaleManager(models.Manager):
    def get_queryset(self):
        # Only allow dill nights that are on sale, the cut_off time is in the future
        # and the drill night is within the next 4 weeks
        return (
            super()
            .get_queryset()
            .filter(
                cut_off_time__gt=datetime.now(timezone.utc),
                date_time__lt=datetime.now(timezone.utc) + timedelta(weeks=4),
                on_sale=True,
            )
        )


class DrillNight(models.Model):

    objects = models.Manager()
    sellable = OnSaleManager()

    date_time = models.DateTimeField()
    cut_off_time = models.DateTimeField()

    on_sale = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.date_time.strftime("%a %d %b (%H:%M)")

    def is_before_cut_off_time(self) -> bool:
        return datetime.now(timezone.utc) < self.cut_off_time


class TransactionRecord(models.Model):
    class PaymentStatus(models.TextChoices):
        AWAITING_CHECKOUT = (
            "awaiting_checkout",
            "Awaiting Checkout",
        )  # The user has started the checkout process
        PAID = "paid", "Paid"  # The user completed the checkout process
        REFUNDED = (
            "refunded",
            "Refunded",
        )  # The transaction has been refunded after the payment being placed
        CANCELLED = (
            "cancelled",
            "Cancelled",
        )  # The user actively cancelled during the checkout process

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    status = models.CharField(
        choices=PaymentStatus.choices,
        max_length=31,
        default=PaymentStatus.AWAITING_CHECKOUT,
    )

    drill_night = models.ForeignKey(DrillNight, on_delete=models.CASCADE)

    name = models.CharField(max_length=512)
    email = models.EmailField()

    quantity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], default=1
    )
    dietary_notes = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.name} - {self.drill_night}"

    def get_absolute_url(self):
        return reverse("drill_suppers:detail", args=[self.id])

    def refund(self):

        if not self.drill_night.is_before_cut_off_time():
            raise AfterDrillNightCutOffError

        session = self.stripecheckoutsession.get_session()

        stripe.Refund.create(payment_intent=session.payment_intent)

        self.status = TransactionRecord.PaymentStatus.REFUNDED
        self.save()


class StripeCheckoutSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_record = models.OneToOneField(
        TransactionRecord, on_delete=models.CASCADE
    )

    session_id = models.CharField(max_length=256, null=True, blank=True)
    checkout_url = models.TextField(null=True, blank=True)

    def get_session(self):
        return stripe.checkout.Session.retrieve(self.session_id)

    def generate_session(self) -> None:

        if self.session_id and self.checkout_url:
            return

        checkout_session = stripe.checkout.Session.create(
            success_url=f"{SERVER_URL}/supper/{self.transaction_record.id}/purchased?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{SERVER_URL}/supper/{self.transaction_record.id}/cancel?session_id={{CHECKOUT_SESSION_ID}}",
            mode="payment",
            client_reference_id=self.transaction_record.id,
            customer_email=self.transaction_record.email,
            line_items=[
                {
                    "price_data": {
                        "currency": "GBP",
                        "product_data": {
                            "name": f"Drill Supper on {self.transaction_record.drill_night}",
                        },
                        "tax_behavior": "inclusive",
                        "unit_amount": 500,
                    },
                    "quantity": self.transaction_record.quantity,
                },
            ],
        )

        print(checkout_session.id)
        print(checkout_session.url)

        self.session_id = checkout_session.id
        self.checkout_url = checkout_session.url

        self.save()

    def verify_if_paid(self) -> bool:
        return self.get_session().payment_status == "paid"
