from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import index

urlpatterns = [
    path('', index, name='home'),
    path('admin/', admin.site.urls),

    # frontend product pages
    path('books/', include(('products.urls', 'products'), namespace='products')),

    # API base
    path('api/books/', include(('products.urls', 'products_api'), namespace='products_api')),

    # cart
    path('cart/', include(('products.cart_urls', 'product_cart'), namespace='product_cart')),

    # orders (checkout flow)
    path('orders/', include(('orders.urls', 'orders'), namespace='orders')),
]

# Serve static and media files in development
if settings.DEBUG:
    from pathlib import Path
    # Create a temporary settings dict for static() to use
    static_dir = Path(__file__).resolve().parent.parent / 'staticfiles'
    # Use static() from django.conf.urls which properly serves from a directory
    urlpatterns += static(settings.STATIC_URL, document_root=str(static_dir))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
