from django.urls import path
from .views import cart_view, add_to_cart, update_cart, remove_from_cart

urlpatterns = [
    path('', cart_view, name='cart'),
    path('add/', add_to_cart, name='add_to_cart'),
    path('update/', update_cart, name='update_cart'),
    path('remove/', remove_from_cart, name='remove_from_cart'),
]
