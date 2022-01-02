import random
from datetime import timedelta

from factory import Factory, Faker, LazyAttribute, LazyFunction, SubFactory
from factory.django import DjangoModelFactory

from hac_shop.drill_suppers.models import (
    DrillNight,
    StripeCheckoutSession,
    TransactionRecord,
)


class MockStripeSessionObject:
    id: str
    url: str
    payment_status: str
    payment_intent: str

    def __init__(self, id, url, payment_status, payment_intent) -> None:
        self.id = id
        self.url = url
        self.payment_status = payment_status
        self.payment_intent = payment_intent


class StripeCheckoutSessionObjectFactory(Factory):
    id = Faker("word")
    url = Faker("url")
    payment_status = LazyFunction(
        lambda: random.choice(["paid", "unpaid", "no_payment_required"])
    )
    payment_intent = Faker("word")

    class Meta:
        model = MockStripeSessionObject


class DrillNightFactory(DjangoModelFactory):
    date_time = Faker("future_datetime")
    cut_off_time = LazyAttribute(lambda o: o.date_time - timedelta(hours=2))

    class Meta:
        model = DrillNight


class TransactionRecordFactory(DjangoModelFactory):
    drill_night = SubFactory(DrillNightFactory)

    name = Faker("first_name")
    email = Faker("email")

    quantity = LazyFunction(lambda: random.randrange(1, 5))
    dietary_notes = Faker("sentence")

    class Meta:
        model = TransactionRecord


class StripeCheckoutSessionFactory(DjangoModelFactory):
    transaction_record = SubFactory(TransactionRecordFactory)

    class Meta:
        model = StripeCheckoutSession
