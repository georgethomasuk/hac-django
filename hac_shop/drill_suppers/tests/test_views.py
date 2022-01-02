from unittest import mock

import pytest
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest
from django.test import RequestFactory
from django.urls import reverse
from faker import Faker

from hac_shop.drill_suppers.forms import PurchaseForm
from hac_shop.drill_suppers.models import StripeCheckoutSession, TransactionRecord
from hac_shop.drill_suppers.tests.factories import MockStripeSessionObject
from hac_shop.drill_suppers.views import (
    TransactionRecordCancelled,
    TransactionRecordCreate,
    TransactionRecordPurchased,
)
from hac_shop.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

fake = Faker()


class TestCreateTransactionRecordView:
    @mock.patch("stripe.checkout.Session.create")
    def test_post(
        self,
        create_mock,
        stripe_checkout_session_object: MockStripeSessionObject,
        transaction_record: TransactionRecord,
        rf: RequestFactory,
    ):

        create_mock.return_value = stripe_checkout_session_object

        email = fake.email()

        request = rf.post(
            "/supper/",
            {
                "name": transaction_record.name,
                "email": email,
                "status": transaction_record.status,
                "drill_night": transaction_record.drill_night.pk,
                "quantity": transaction_record.quantity,
                "dietary_notes": transaction_record.dietary_notes,
            },
        )

        response = TransactionRecordCreate.as_view()(request)

        assert response.status_code == 302
        assert response.url == stripe_checkout_session_object.url

        created_transaction_record = TransactionRecord.objects.get(email=email)
        assert created_transaction_record.email == email
        assert (
            created_transaction_record.status
            == TransactionRecord.PaymentStatus.AWAITING_CHECKOUT
        )
        assert (
            created_transaction_record.stripecheckoutsession.checkout_url
            == response.url
        )


class TestTransactionRecordPurchasedView:
    @mock.patch("stripe.checkout.Session.retrieve")
    @mock.patch("stripe.checkout.Session.create")
    def test_get(
        self,
        create_session_mock,
        retrieve_session_mock,
        stripe_checkout_session_object: MockStripeSessionObject,
        stripe_checkout_session: StripeCheckoutSession,
        rf: RequestFactory,
    ):

        transaction_record = stripe_checkout_session.transaction_record

        create_session_mock.return_value = stripe_checkout_session_object
        retrieve_session_mock.return_value = stripe_checkout_session_object

        stripe_checkout_session.generate_session()

        view = TransactionRecordPurchased.as_view()

        # without a session id returns a 400
        request = rf.get(f"/supper/{transaction_record.id}/purchased")
        response = view(request, pk=transaction_record.id)

        assert response.status_code == 400

        # with a mis matched session id returns a 400
        request = rf.get(f"/supper/{transaction_record.id}/purchased?session_id=123")
        response = view(request, pk=transaction_record.id)

        assert response.status_code == 400

        # with matching data but status is not paid return a 400
        stripe_checkout_session_object.payment_status = "unpaid"
        request = rf.get(
            f"/supper/{transaction_record.id}/purchased?session_id={transaction_record.stripecheckoutsession.session_id}"
        )
        response = view(request, pk=transaction_record.id)

        assert response.status_code == 400

        # when all matching a paid, redirects to success page
        stripe_checkout_session_object.payment_status = "paid"
        request = rf.get(
            f"/supper/{transaction_record.id}/purchased?session_id={transaction_record.stripecheckoutsession.session_id}"
        )
        response = view(request, pk=transaction_record.id)

        assert response.status_code == 302
        assert response.url == transaction_record.get_absolute_url()


class TestTransactionRecordCancelledView:
    @mock.patch("stripe.checkout.Session.retrieve")
    @mock.patch("stripe.checkout.Session.create")
    def test_get(
        self,
        create_session_mock,
        retrieve_session_mock,
        stripe_checkout_session_object: MockStripeSessionObject,
        stripe_checkout_session: StripeCheckoutSession,
        rf: RequestFactory,
    ):

        transaction_record = stripe_checkout_session.transaction_record

        create_session_mock.return_value = stripe_checkout_session_object
        retrieve_session_mock.return_value = stripe_checkout_session_object

        stripe_checkout_session.generate_session()

        view = TransactionRecordCancelled.as_view()

        # without a session id returns a 400
        request = rf.get(f"/supper/{transaction_record.id}/purchased")
        response = view(request, pk=transaction_record.id)

        assert response.status_code == 400

        # with a mis matched session id returns a 400
        request = rf.get(f"/supper/{transaction_record.id}/purchased?session_id=123")
        response = view(request, pk=transaction_record.id)

        assert response.status_code == 400

        # with matching data but status is not paid return a 400
        stripe_checkout_session_object.payment_status = "unpaid"
        request = rf.get(
            f"/supper/{transaction_record.id}/purchased?session_id={transaction_record.stripecheckoutsession.session_id}"
        )
        response = view(request, pk=transaction_record.id)

        assert response.status_code == 400

        # when all matching a paid, redirects to success page
        stripe_checkout_session_object.payment_status = "paid"
        request = rf.get(
            f"/supper/{transaction_record.id}/purchased?session_id={transaction_record.stripecheckoutsession.session_id}"
        )
        response = view(request, pk=transaction_record.id)

        assert response.status_code == 302
        assert response.url == "/supper/"
