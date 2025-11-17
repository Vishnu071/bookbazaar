from django.urls import path
from .views import checkout, create_order, verify_payment, order_success

app_name = "orders"

urlpatterns = [
    path('checkout/', checkout, name='checkout'),
    path('create/', create_order, name='create_order'),
    path('verify/', verify_payment, name='verify_payment'),
    path('success/<int:order_id>/', order_success, name='order_success'),
]
