from datetime import datetime, timedelta, timezone

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Div, Field, Fieldset, Layout, Submit
from django.core.exceptions import ValidationError
from django.forms import EmailField, Form, ModelForm

from .models import DrillNight, StripeCheckoutSession, TransactionRecord


class PurchaseForm(ModelForm):
    class Meta:
        model = TransactionRecord
        fields = ["name", "email", "drill_night", "quantity", "dietary_notes"]

        labels = {
            "name": "Your name",
            "email": "Your email",
            "quantity": "How many meals?",
            "dietary_notes": "Any dietary requirements",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only show sellable drill nights
        self.fields["drill_night"].queryset = DrillNight.sellable.all()

        self.helper = FormHelper()
        self.helper.form_method = "POST"
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Div(
                            Field("name"),
                            Field("email"),
                            css_class="card-body p-4",
                        ),
                        css_class="card",
                    ),
                    css_class="col",
                ),
                css_class="row mb-3",
            ),
            Div(
                Div(
                    Div(
                        Div(
                            Field("drill_night"),
                            Field("quantity"),
                            Field("dietary_notes"),
                            css_class="card-body p-4",
                        ),
                        css_class="card",
                    ),
                    css_class="col",
                ),
                css_class="row mb-3",
            ),
            Div(
                Submit("submit", "Buy", css_class="col"),
                css_class="row p-3 mb-5",
            ),
        )

    def save(self, commit: bool = True):
        obj = super().save(commit=commit)

        if commit:
            StripeCheckoutSession.objects.create(transaction_record=obj)

        return obj


class RefundForm(ModelForm):

    confirm_email = EmailField(label="Enter the email you used to book the meal")

    class Meta:
        model = TransactionRecord
        fields = ["confirm_email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = "POST"
        self.helper.layout = Layout(
            Field("confirm_email"),
            Submit("submit", "Cancel and Refund", css_class="btn-danger"),
        )

    def clean_confirm_email(self):
        data = self.cleaned_data["confirm_email"]
        if data != self.instance.email:
            raise ValidationError("This email is not the one used to book the meal")

        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return data
