# Combined API (DRF) + page views + session-based cart views
from rest_framework import generics, filters
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Book
from .serializers import BookSerializer

# ---- DRF API views ----
class BookListAPIView(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'author', 'description']
    ordering_fields = ['price', 'created_at']

class BookDetailAPIView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    lookup_field = 'slug'

# ---- Server-rendered page views ----
def product_list(request):
    q = request.GET.get('q', '').strip()
    books_qs = Book.objects.all()
    if q:
        books_qs = books_qs.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(description__icontains=q))

    order = request.GET.get('order', '')
    if order == 'price_asc':
        books_qs = books_qs.order_by('price')
    elif order == 'price_desc':
        books_qs = books_qs.order_by('-price')

    page = request.GET.get('page', 1)
    paginator = Paginator(books_qs, 9)
    try:
        books = paginator.get_page(page)
    except:
        books = paginator.get_page(1)

    context = {
        'books': books,
        'q': q,
        'paginator': paginator,
    }
    return render(request, 'products/product_list.html', context)

def product_detail(request, slug):
    book = get_object_or_404(Book, slug=slug)
    return render(request, 'products/product_detail.html', {'book': book})

# ---- Session-based cart helpers ----
def _get_cart(session):
    return session.get('cart', {})

def _save_cart(session, cart):
    session['cart'] = cart
    session.modified = True

# ---- Cart views ----
@require_POST
def add_to_cart(request):
    slug = request.POST.get('slug')
    qty = int(request.POST.get('quantity', 1))
    book = get_object_or_404(Book, slug=slug)

    cart = _get_cart(request.session)
    item = cart.get(slug)
    if item:
        item['quantity'] = item.get('quantity', 0) + qty
    else:
        cart[slug] = {
            'id': book.id,
            'title': book.title,
            'price': float(book.price),
            'quantity': qty
        }
    _save_cart(request.session, cart)
    # default redirect to product list (namespaced)
    return redirect(request.POST.get('next', reverse('products:product-list')))

@require_POST
def update_cart(request):
    slug = request.POST.get('slug')
    qty = int(request.POST.get('quantity', 0))
    cart = _get_cart(request.session)
    if slug in cart:
        if qty > 0:
            cart[slug]['quantity'] = qty
        else:
            cart.pop(slug, None)
    _save_cart(request.session, cart)
    # default redirect to cart (namespaced)
    return redirect(request.POST.get('next', reverse('product_cart:cart')))

@require_POST
def remove_from_cart(request):
    slug = request.POST.get('slug')
    cart = _get_cart(request.session)
    if slug in cart:
        cart.pop(slug, None)
    _save_cart(request.session, cart)
    return redirect(request.POST.get('next', reverse('product_cart:cart')))

def cart_view(request):
    cart = _get_cart(request.session)
    items = []
    total = 0.0
    for slug, data in cart.items():
        qty = int(data.get('quantity', 0))
        price = float(data.get('price', 0.0))
        subtotal = qty * price
        items.append({'slug': slug, 'title': data.get('title'), 'price': price, 'quantity': qty, 'subtotal': subtotal})
        total += subtotal
    return render(request, 'cart.html', {'items': items, 'total': total})
