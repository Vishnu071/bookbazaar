import os
import razorpay

print("ENV KEYS PRESENT:", bool(os.environ.get("RAZORPAY_KEY_ID")), bool(os.environ.get("RAZORPAY_KEY_SECRET")))
print("KEY ID (first 20 chars):", (os.environ.get("RAZORPAY_KEY_ID") or "")[:20])
print("KEY SECRET LENGTH:", len(os.environ.get("RAZORPAY_KEY_SECRET") or ""))

client = razorpay.Client(auth=(
    os.environ.get("RAZORPAY_KEY_ID"),
    os.environ.get("RAZORPAY_KEY_SECRET")
))

try:
    order = client.order.create({"amount": 100, "currency": "INR", "payment_capture": "0"})
    print("SUCCESS — ORDER CREATED:", order.get("id"))
except Exception as e:
    print("ERROR TYPE:", type(e).__name__)
    print("ERROR DETAILS:", e)
