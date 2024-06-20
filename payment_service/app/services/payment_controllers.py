from sqlmodel import select
import stripe
from fastapi import HTTPException
from fastapi import FastAPI


from app.models.payment_models import AdvancePayment, Payment, PaymentForm, RemainingPaymentModel
from app.models.order_models import Order
from app.db.db_connector import DB_SESSION
from app.services.payment_services import (read_payment_details, read_advance_payment,
                                                handle_ready_made_payment, handle_booking_payment, handle_remaining_payment)

app = FastAPI()

stripe.api_key = "your api key"

def process_payment(payment_details: PaymentForm, session: DB_SESSION):
    # Fetch the order from the database
    order = session.get(Order, payment_details.order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order not found for order ID: {
                            payment_details.order_id}"
                            )

    try:
        # Handle booking and ready-made orders differently
        if order.order_type == "Booking":
            handle_booking_payment(payment_details, order, session)
        elif order.order_type == "Ready made":
            handle_ready_made_payment(payment_details, order, session)
        else:
            raise HTTPException(status_code=400, detail="Invalid order type.")
    except stripe.StripeError as se:
        raise HTTPException(status_code=500, detail=str(se))
    
@app.post('/create-checkout-session')
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                     'price': 'price_1PShL1If22jmWnXxW8BRw0jI',
                    'quantity': 1,
                },
            ],
            mode='subscription',
            # success_url=YOUR_DOMAIN + '/success.html',
            # cancel_url=YOUR_DOMAIN + '/cancel.html',
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



def delete_payment(order_id: int, session: DB_SESSION):
    payment_table = read_payment_details(order_id, session)
    payment_table.advance_payment = None
    session.delete(payment_table)
    session.commit()
    return f"Payment has been successfully deleted for order {order_id}."