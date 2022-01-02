from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

from hac_shop.drill_suppers.models import (
    AfterDrillNightCutOffError,
    DrillNight,
    StripeCheckoutSession,
    TransactionRecord,
)
from hac_shop.drill_suppers.tests.factories import MockStripeSessionObject

pytestmark = pytest.mark.django_db


class TestDrillNight:
    def test_string_representation(self, drill_night: DrillNight):

        drill_night.date_time = datetime(1988, 2, 22, 19, 0, tzinfo=timezone.utc)

        assert str(drill_night) == "Mon 22 Feb (19:00)"

    def test_is_before_cut_off_time(self, drill_night: DrillNight):

        # Asset that if the cut off time is in the past, then the method
        # returns false
        drill_night.cut_off_time = datetime.now(timezone.utc) - timedelta(seconds=1)
        assert drill_night.is_before_cut_off_time() == False

        # Asset that if the cut off time is in the future, then the method
        # returns false
        drill_night.cut_off_time = datetime.now(timezone.utc) + timedelta(seconds=1)
        assert drill_night.is_before_cut_off_time() == True

    def test_sellable(self, drill_night: DrillNight):

        # Not included if not on sale
        drill_night.on_sale = False
        drill_night.date_time = datetime.now(timezone.utc) + timedelta(weeks=1)
        drill_night.cut_off_time = datetime.now(timezone.utc) + timedelta(seconds=1)
        drill_night.save()

        assert DrillNight.sellable.filter(pk=drill_night.pk).exists() == False

        # Not included if more than 4 weeks into the future
        drill_night.on_sale = True
        drill_night.date_time = (
            datetime.now(timezone.utc) + timedelta(weeks=4) + timedelta(seconds=1)
        )
        drill_night.cut_off_time = datetime.now(timezone.utc) + timedelta(seconds=1)
        drill_night.save()

        assert DrillNight.sellable.filter(pk=drill_night.pk).exists() == False

        # Not included if cut_off is in the past
        drill_night.on_sale = True
        drill_night.date_time = datetime.now(timezone.utc) + timedelta(weeks=1)
        drill_night.cut_off_time = datetime.now(timezone.utc) - timedelta(seconds=1)
        drill_night.save()

        assert DrillNight.sellable.filter(pk=drill_night.pk).exists() == False

        # Otherwise included
        drill_night.on_sale = True
        drill_night.date_time = datetime.now(timezone.utc) + timedelta(weeks=1)
        drill_night.cut_off_time = datetime.now(timezone.utc) + timedelta(seconds=1)
        drill_night.save()

        assert DrillNight.sellable.filter(pk=drill_night.pk).exists() == True


class TestTransactionRecord:
    def test_user_get_absolute_url(self, transaction_record: TransactionRecord):
        assert (
            transaction_record.get_absolute_url() == f"/supper/{transaction_record.id}/"
        )

    @mock.patch("stripe.Refund.create")
    @mock.patch("stripe.checkout.Session.retrieve")
    def test_refundd(
        self,
        session_retrieve_mock,
        refund_create_mock,
        stripe_checkout_session_object: MockStripeSessionObject,
        stripe_checkout_session: StripeCheckoutSession,
    ):

        session_retrieve_mock.return_value = stripe_checkout_session_object

        transaction_record = stripe_checkout_session.transaction_record

        # Raises error if after the cutoff period
        with pytest.raises(AfterDrillNightCutOffError):
            transaction_record.drill_night.cut_off_time = datetime.now(
                tz=timezone.utc
            ) - timedelta(seconds=1)
            transaction_record.drill_night.save()
            transaction_record.refund()

        transaction_record.drill_night.cut_off_time = datetime.now(
            tz=timezone.utc
        ) + timedelta(hours=1)
        transaction_record.drill_night.save()
        transaction_record.refund()

        assert transaction_record.status == TransactionRecord.PaymentStatus.REFUNDED


class TestStripeCheckoutSession:
    @mock.patch("stripe.checkout.Session.create")
    def test_generate_session(
        self,
        create_mock,
        stripe_checkout_session_object: MockStripeSessionObject,
        stripe_checkout_session: StripeCheckoutSession,
    ):

        create_mock.return_value = stripe_checkout_session_object

        # Starts with no session data
        assert stripe_checkout_session.session_id is None
        assert stripe_checkout_session.checkout_url is None

        # Generate a new session and sets the critical params
        stripe_checkout_session.generate_session()
        assert stripe_checkout_session.session_id is stripe_checkout_session_object.id
        assert (
            stripe_checkout_session.checkout_url is stripe_checkout_session_object.url
        )

        # Re-uses the data if regenerated
        original_session_id = stripe_checkout_session.session_id
        original_checkout_url = stripe_checkout_session.checkout_url

        stripe_checkout_session.generate_session()
        assert stripe_checkout_session.session_id is original_session_id
        assert stripe_checkout_session.checkout_url is original_checkout_url

    @mock.patch("stripe.checkout.Session.retrieve")
    def test_verify_if_paid(
        self,
        retrieve_mock,
        stripe_checkout_session_object: MockStripeSessionObject,
        stripe_checkout_session: StripeCheckoutSession,
    ):

        retrieve_mock.return_value = stripe_checkout_session_object

        stripe_checkout_session_object.payment_status = "unpaid"
        assert stripe_checkout_session.verify_if_paid() == False

        stripe_checkout_session_object.payment_status = "no_payment_required"
        assert stripe_checkout_session.verify_if_paid() == False

        stripe_checkout_session_object.payment_status = "paid"
        assert stripe_checkout_session.verify_if_paid() == True
