import pytest

from hac_shop.drill_suppers.models import (
    DrillNight,
    StripeCheckoutSession,
    TransactionRecord,
)
from hac_shop.drill_suppers.tests.factories import (
    DrillNightFactory,
    MockStripeSessionObject,
    StripeCheckoutSessionFactory,
    StripeCheckoutSessionObjectFactory,
    TransactionRecordFactory,
)
from hac_shop.users.models import User
from hac_shop.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user() -> User:
    return UserFactory()


@pytest.fixture
def transaction_record() -> TransactionRecord:
    return TransactionRecordFactory()


@pytest.fixture
def drill_night() -> DrillNight:
    return DrillNightFactory()


@pytest.fixture
def stripe_checkout_session() -> StripeCheckoutSession:
    return StripeCheckoutSessionFactory()


@pytest.fixture
def stripe_checkout_session_object() -> MockStripeSessionObject:
    return StripeCheckoutSessionObjectFactory()
