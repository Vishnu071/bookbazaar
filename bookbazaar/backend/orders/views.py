from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.http import HttpResponse
import razorpay
from decimal import Decimal

# Import models defensively
try:
    from .models import Order, OrderItem
except Exception:
    Order = None
    OrderItem = None

try:
    from products.models import Book
except Exception:
    Book = None

def _get_cart_from_session(request):
    """
    Expected session cart format:
      request.session['cart'] = { '<book_slug>': { 'qty': 2, 'price': 19900, 'title': '...' }, ... }
    """
    return request.session.get('cart', {})

def checkout(request):
    """
    Show checkout page. Reads cart from session and computes total.
    """
    cart = _get_cart_from_session(request)
    items = []
    total = Decimal('0.00')
    for slug, data in cart.items():
        qty = int(data.get('qty', 1))
        price_paise = int(data.get('price', 0))
        subtotal = price_paise * qty
        total += Decimal(price_paise) * qty
        items.append({
            'slug': slug,
            'title': data.get('title', ''),
            'qty': qty,
            'price_paise': price_paise,
            'subtotal_paise': int(subtotal),
        })

    amount_display = f"{(total/100):.2f}"
    context = {
        'items': items,
        'total': int(total),           # in paise
        'total_display': amount_display
    }
    return render(request, 'checkout.html', context)

@require_POST
def create_order(request):
    """
    Create Order in DB (if model exists), create Razorpay order, render payment page.
    """
    cart = _get_cart_from_session(request)
    if not cart:
        return redirect('products:product-list')

    full_name = request.POST.get('full_name', '').strip()
    email = request.POST.get('email', '').strip()
    address = request.POST.get('address', '').strip()

    total_paise = 0
    for slug, data in cart.items():
        qty = int(data.get('qty', 1))
        price_paise = int(data.get('price', 0))
        total_paise += price_paise * qty

    order = None
    if Order is not None:
        try:
            # create DB order (fields may vary — adjust if needed)
            kwargs = {}
            # best-effort fields; adapt if your Order model differs
            if hasattr(Order, 'full_name'):
                kwargs['full_name'] = full_name or "N/A"
            if hasattr(Order, 'email'):
                kwargs['email'] = email or "N/A"
            if hasattr(Order, 'address'):
                kwargs['address'] = address or "N/A"
            if hasattr(Order, 'total'):
                # store total in rupees if total field expects that
                kwargs['total'] = (total_paise // 100)
            order = Order.objects.create(**kwargs)
            # try to create OrderItems
            if OrderItem is not None:
                for slug, data in cart.items():
                    qty = int(data.get('qty', 1))
                    price_paise = int(data.get('price', 0))
                    title = data.get('title', '')
                    try:
                        fields = {}
                        if hasattr(OrderItem, 'order'):
                            fields['order'] = order
                        if hasattr(OrderItem, 'product_id'):
                            fields['product_id'] = data.get('product_id', None)
                        if hasattr(OrderItem, 'title'):
                            fields['title'] = title
                        if hasattr(OrderItem, 'price'):
                            fields['price'] = int(price_paise)
                        if hasattr(OrderItem, 'quantity'):
                            fields['quantity'] = qty
                        if hasattr(OrderItem, 'subtotal'):
                            fields['subtotal'] = int(price_paise * qty)
                        OrderItem.objects.create(**fields)
                    except Exception:
                        # ignore item creation errors to keep flow moving
                        pass
        except Exception as e:
            print("Warning: could not create Order model instance:", e)
            order = None

    client = razorpay.Client(auth=(getattr(settings, 'RAZORPAY_KEY_ID', ''), getattr(settings, 'RAZORPAY_KEY_SECRET', '')))

    try:
        razor_amount = int(total_paise)  # paise
        razor_order = client.order.create(dict(amount=razor_amount, currency='INR', payment_capture='0'))
        razorpay_order_id = razor_order.get('id')
        if order is not None:
            try:
                if hasattr(order, 'razorpay_order_id'):
                    order.razorpay_order_id = razorpay_order_id
                    order.save()
            except Exception:
                pass
    except Exception as e:
        return render(request, 'order_failed.html', {'error_message': f'Razorpay order creation failed: {e}'})

    context = {
        'order': order or {'id': 'TEMP'},
        'amount': razor_amount,
        'amount_display': f"{(razor_amount/100):.2f}",
        'razorpay_order': razor_order,
        'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', ''),
    }
    return render(request, 'payment_page.html', context)


@require_POST
def verify_payment(request):
    """
    Verify Razorpay signature and capture payment using exact razor order amount.
    """
    order_id = request.POST.get('order_id') or request.POST.get('order_id')
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_signature = request.POST.get('razorpay_signature')

    if not (order_id and razorpay_payment_id and razorpay_order_id and razorpay_signature):
        return render(request, 'order_failed.html', {'error_message': 'Missing payment parameters.'})

    client = razorpay.Client(auth=(getattr(settings, 'RAZORPAY_KEY_ID', ''), getattr(settings, 'RAZORPAY_KEY_SECRET', '')))

    params = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }

    try:
        client.utility.verify_payment_signature(params)
    except Exception as e:
        return render(request, 'order_failed.html', {'error_message': f'Payment signature verification failed: {e}'})

    # SAFER CAPTURE: fetch razor order to get exact amount expected, then capture that amount
    try:
        try:
            razor_order = client.order.fetch(razorpay_order_id)
            razor_amount = int(razor_order.get('amount', 0))  # amount in paise
        except Exception as e:
            razor_order = None
            razor_amount = None
            print("Warning: could not fetch razor order:", e)

        amount_to_capture = None
        if Order is not None:
            try:
                order_obj = get_object_or_404(Order, id=order_id)
                if hasattr(order_obj, 'total') and order_obj.total is not None:
                    db_amount_paise = int(order_obj.total) * 100
                    if razor_amount and db_amount_paise != razor_amount:
                        print(f"Notice: DB amount ({db_amount_paise}) != razor amount ({razor_amount}); using razor amount for capture")
                    amount_to_capture = razor_amount or db_amount_paise
            except Exception:
                pass

        if amount_to_capture is None:
            amount_to_capture = razor_amount or 0

        if not amount_to_capture:
            raise Exception("Could not determine amount to capture (amount is 0).")

        client.payment.capture(razorpay_payment_id, amount_to_capture)
    except Exception as e:
        print("Warning: capture failed:", e)

    # update DB order if exists
    if Order is not None:
        try:
            order_obj = get_object_or_404(Order, id=order_id)
            if hasattr(order_obj, 'razorpay_order_id'):
                order_obj.razorpay_order_id = razorpay_order_id
            if hasattr(order_obj, 'razorpay_payment_id'):
                order_obj.razorpay_payment_id = razorpay_payment_id
            if hasattr(order_obj, 'status'):
                try:
                    order_obj.status = 'PAID'
                except Exception:
                    pass
            order_obj.save()
        except Exception as e:
            return render(request, 'order_failed.html', {'error_message': f'Could not update order record: {e}'})

    try:
        del request.session['cart']
        request.session.modified = True
    except Exception:
        pass

    if Order is not None:
        return redirect('orders:order_success', order_id=order_id)
    else:
        return render(request, 'order_success.html', {'order': {'id': order_id}})

def order_success(request, order_id):
    order_obj = None
    if Order is not None:
        try:
            order_obj = get_object_or_404(Order, id=order_id)
        except Exception:
            order_obj = None
    return render(request, 'order_success.html', {'order': order_obj or {'id': order_id}})
