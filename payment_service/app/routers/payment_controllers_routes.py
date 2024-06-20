from sqlmodel import select
import stripe
from fastapi import HTTPException
from fastapi import FastAPI



from app.models.payment_models import AdvancePayment, Payment, PaymentForm, RemainingPaymentModel
from app.models.order_models import Order
from app.db.db_connector import DB_SESSION
from app.services.payment_services import (read_payment_details, read_advance_payment,
                                                handle_ready_made_payment, handle_booking_payment, handle_remaining_payment)

router = APIRouter()


payment_router = APIRouter()

@payment_router.post("/create_payment/", response_model=Order)
def create_payment(payment_details: PaymentForm, session: DB_SESSION):
    try:
        # Fetch the order from the database
        order = session.get(Order, payment_details.order_id)
        if not order:
            raise HTTPException(status_code=404, detail=f"Order not found for order ID: {payment_details.order_id}")

        # Handle booking and ready-made orders differently
        if order.order_type == "Booking":
            handle_booking_payment(payment_details, order, session)
        elif order.order_type == "Ready made":
            handle_ready_made_payment(payment_details, order, session)
        else:
            raise HTTPException(status_code=400, detail="Invalid order type.")

        return order
    except stripe.StripeError as se:
        raise HTTPException(status_code=500, detail=str(se))
