from django.urls import path

from . import views

app_name = "drill_suppers"
urlpatterns = [
    # ex: /polls/
    path("", views.TransactionRecordCreate.as_view(), name="index"),
    path("<pk>/", views.TransactionRecordDetail.as_view(), name="detail"),
    path(
        "<pk>/purchased", views.TransactionRecordPurchased.as_view(), name="purchased"
    ),
    path("<pk>/cancel", views.TransactionRecordCancelled.as_view(), name="cancel"),
    path("<pk>/refund", views.TransactionRecordRefund.as_view(), name="refund"),
]
