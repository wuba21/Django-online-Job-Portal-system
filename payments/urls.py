from django.urls import path
from .views import initiate_checkout, payment_callback, pricing_page

app_name = "payments"

urlpatterns = [
    path("pricing/", pricing_page, name="pricing"),
    path("checkout/", initiate_checkout, name="initiate_checkout"),
    path("callback/", payment_callback, name="payment_callback"),
]
