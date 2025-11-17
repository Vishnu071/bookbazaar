from django.urls import path
from .views import BookListAPIView, BookDetailAPIView, product_list, product_detail

urlpatterns = [
    # API endpoints (if included under /api/books/)
    path('api/', BookListAPIView.as_view(), name='api-book-list'),
    path('api/<slug:slug>/', BookDetailAPIView.as_view(), name='api-book-detail'),

    # Frontend pages (mounted under /books/)
    path('', product_list, name='product-list'),
    path('<slug:slug>/', product_detail, name='product-detail'),
]
