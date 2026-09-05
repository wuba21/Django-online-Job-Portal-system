from django.urls import path
from .views import initiate_checkout, payment_callback, pricing_page

app_name = "payments"

urlpatterns = [
    path("pricing/", pricing_page, name="pricing"),
    path("checkout/", initiate_checkout, name="initiate_checkout"),
    path("checkout/initiate/", initiate_checkout, name="initiate_checkout_alias"),
    path("initiate-checkout/", initiate_checkout, name="initiate_checkout_alias2"),
    path("callback/", payment_callback, name="payment_callback"),
]
