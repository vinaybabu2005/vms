from django.db import transaction
from django.db.models import F
from .models import Order, Product

TRANSITIONS = {
    'placed': {'placed', 'processing', 'shipped', 'cancelled'},
    'processing': {'processing', 'shipped', 'cancelled'},
    'shipped': {'shipped', 'delivered'},
    'delivered': {'delivered'},
    'cancelled': {'cancelled'},
}

def restore_stock(order):
    if order.stock_restored:
        return
    for item in order.items.all():
        if item.product_id:
            Product.objects.filter(pk=item.product_id).update(stock=F('stock') + item.quantity)
    order.stock_restored = True
    order.save(update_fields=['stock_restored'])

@transaction.atomic
def update_order(pk, data):
    order = Order.objects.select_for_update().get(pk=pk)
    status = data['status']
    if status not in TRANSITIONS.get(order.status, set()):
        raise ValueError('This status change is not allowed. Shipped and delivered orders cannot be cancelled.')
    if order.status in ('shipped', 'delivered', 'cancelled'):
        for field in ('full_name', 'phone', 'address'):
            if data.get(field, getattr(order, field)) != getattr(order, field):
                raise ValueError('Delivery details can only be edited before shipping.')
    if status == 'cancelled' and order.status != 'cancelled':
        reason = data.get('cancellation_reason', '')
        if reason not in dict(Order.CANCEL_REASONS):
            raise ValueError('Choose a cancellation reason.')
        restore_stock(order)
        order.cancellation_reason = reason
        order.cancellation_note = data.get('cancellation_note', '')
        from django.utils import timezone
        order.cancelled_at = timezone.now()
    for field in ('status','full_name','phone','address','courier','tracking_number','tracking_url','estimated_delivery','shipping_notes','cancellation_reason','cancellation_note'):
        if field in data:
            setattr(order, field, data[field])
    order.full_clean()
    order.save()
    return order

@transaction.atomic
def cancel_customer_order(pk, user, reason, note=''):
    order = Order.objects.select_for_update().get(pk=pk, user=user)
    if order.status not in ('placed', 'processing'):
        raise ValueError('This order can no longer be cancelled because it is already shipped, delivered, or cancelled.')
    if reason not in dict(Order.CANCEL_REASONS):
        raise ValueError('Choose a cancellation reason.')
    restore_stock(order)
    from django.utils import timezone
    order.status = 'cancelled'
    order.cancellation_reason = reason
    order.cancellation_note = note
    order.cancelled_at = timezone.now()
    order.save(update_fields=['status','cancellation_reason','cancellation_note','cancelled_at','stock_restored'])
    return order

@transaction.atomic
def delete_order(pk):
    order = Order.objects.select_for_update().get(pk=pk)
    if order.status in ('placed', 'processing'):
        restore_stock(order)
    order.delete()
