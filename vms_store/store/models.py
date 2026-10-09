from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
class Category(models.Model):
 name=models.CharField(max_length=80,unique=True)
 def __str__(self): return self.name
class Product(models.Model):
 name=models.CharField(max_length=120)
 description=models.TextField(blank=True)
 price=models.DecimalField(max_digits=10,decimal_places=2,validators=[MinValueValidator(Decimal('0.01'))])
 stock=models.PositiveIntegerField(default=0)
 image=models.ImageField(upload_to='products/',blank=True)
 category=models.ForeignKey(Category,on_delete=models.PROTECT)
 def __str__(self): return self.name
class Order(models.Model):
    CANCEL_REASONS = [
        ('changed_mind', 'I changed my mind'),
        ('ordered_by_mistake', 'I ordered by mistake'),
        ('delivery_time', 'Delivery is taking too long'),
        ('price_changed', 'I found a better price'),
        ('other', 'Other'),
    ]
    STATUS = [
        ('placed', 'Placed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='placed'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    payment_method = models.CharField(
        max_length=30,
        default='Cash on delivery'
    )

    courier = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=120, blank=True)
    tracking_url = models.URLField(blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    shipping_notes = models.TextField(blank=True)
    stock_restored = models.BooleanField(default=False, editable=False)
    cancellation_reason = models.CharField(max_length=32, choices=CANCEL_REASONS, blank=True)
    cancellation_note = models.CharField(max_length=500, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.pk}'
class OrderItem(models.Model):
 order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')
 product=models.ForeignKey(Product,on_delete=models.SET_NULL,null=True)
 name=models.CharField(max_length=120)
 price=models.DecimalField(max_digits=10,decimal_places=2)
 quantity=models.PositiveIntegerField()
 @property
 def subtotal(self): return self.price*self.quantity
