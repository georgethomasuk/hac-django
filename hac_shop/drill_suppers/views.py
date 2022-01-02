from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

from .forms import PurchaseForm, RefundForm
from .models import DrillNight, StripeCheckoutSession, TransactionRecord


class TransactionRecordCreate(CreateView):
    model = TransactionRecord
    form_class = PurchaseForm

    def get_success_url(self) -> str:
        checkout_session = self.object.stripecheckoutsession
        checkout_session.generate_session()
        return checkout_session.checkout_url


class TransactionRecordDetail(DetailView):
    model = TransactionRecord


class TransactionRecordPurchased(DetailView):
    model = TransactionRecord

    def get(self, request, *args: str, **kwargs):
        checkout_session_id = request.GET.get("session_id")

        if not checkout_session_id:
            return JsonResponse({"reason": "no session id"}, status=400)

        transaction_record = self.get_object()
        checkout_session = transaction_record.stripecheckoutsession

        if checkout_session.session_id != checkout_session_id:
            return JsonResponse({"reason": "incorrect session id"}, status=400)

        if checkout_session.verify_if_paid():
            transaction_record.status = TransactionRecord.PaymentStatus.PAID
            transaction_record.save()
            return redirect(transaction_record)
        else:
            return JsonResponse({"reason": "not paid"}, status=400)


class TransactionRecordCancelled(DetailView):
    model = TransactionRecord

    def get(self, request, *args: str, **kwargs):
        checkout_session_id = request.GET.get("session_id")

        if not checkout_session_id:
            return JsonResponse({"reason": "no session id"}, status=400)

        transaction_record = self.get_object()
        checkout_session = transaction_record.stripecheckoutsession

        if checkout_session.session_id != checkout_session_id:
            return JsonResponse({"reason": "incorrect session id"}, status=400)

        if checkout_session.verify_if_paid():
            transaction_record.status = TransactionRecord.PaymentStatus.CANCELLED
            transaction_record.save()
            return redirect(reverse("drill_suppers:index"))
        else:
            return JsonResponse({"reason": "not paid"}, status=400)


class TransactionRecordRefund(UpdateView):
    model = TransactionRecord
    form_class = RefundForm
    template_name = "drill_suppers/transactionrecord_refund.html"

    def form_valid(self, form):
        self.object.refund()
        return redirect(self.object)


@method_decorator(staff_member_required, name='dispatch')
class DrillNightReport(DetailView):
    model = DrillNight
