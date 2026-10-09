from decimal import Decimal, InvalidOperation
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import F
from .models import Category,Product,Order,OrderItem
from .forms import CheckoutForm
def cart_count(request): return {'cart_count':sum(request.session.get('cart',{}).values())}
def cart_rows(request):
 cart=request.session.get('cart',{})
 rows=[]
 for p in Product.objects.filter(pk__in=cart):
  q=cart[str(p.pk)];rows.append({'product':p,'quantity':q,'subtotal':p.price*q})
 return rows,sum((r['subtotal'] for r in rows),Decimal('0'))
def home(request):
 products=Product.objects.select_related('category').order_by('id')
 q=request.GET.get('q','').strip();cat=request.GET.get('category','')
 if q: products=products.filter(name__icontains=q)
 if cat.isdigit(): products=products.filter(category_id=cat)
 for param,lookup in [('min','price__gte'),('max','price__lte')]:
  try:
   value=Decimal(request.GET.get(param,''))
   if value.is_finite() and value>=0: products=products.filter(**{lookup:value})
  except InvalidOperation: pass
 return render(request,'home.html',{'products':products,'categories':Category.objects.all(),'q':q,'selected':cat})
def detail(request,pk): return render(request,'detail.html',{'product':get_object_or_404(Product,pk=pk)})
@require_POST
def add(request,pk):
 p=get_object_or_404(Product,pk=pk);cart=request.session.get('cart',{});key=str(pk)
 if cart.get(key,0)<p.stock:
  cart[key]=cart.get(key,0)+1;request.session['cart']=cart;messages.success(request,'Added to your cart.')
 else: messages.error(request,'No more stock available.')
 return redirect('cart')
@require_POST
def update(request,pk):
 cart=request.session.get('cart',{});key=str(pk)
 if request.POST.get('action')=='remove': cart.pop(key,None)
 else:
  p=get_object_or_404(Product,pk=pk)
  try: q=int(request.POST.get('quantity',1))
  except ValueError: q=1
  if q<1: cart.pop(key,None)
  elif q>p.stock: messages.error(request,'Quantity exceeds available stock.')
  else: cart[key]=q
 request.session['cart']=cart
 return redirect('cart')
def cart(request):
 rows,total=cart_rows(request);return render(request,'cart.html',{'rows':rows,'total':total})
def register(request):
 form=UserCreationForm(request.POST or None)
 if request.method=='POST' and form.is_valid():
  login(request,form.save());return redirect('home')
 return render(request,'auth.html',{'form':form,'title':'Create your account','button':'Create account'})
@login_required
def checkout(request):
 rows,total=cart_rows(request)
 if not rows: messages.info(request,'Your cart is empty.');return redirect('cart')
 form=CheckoutForm(request.POST or None)
 if request.method=='POST' and form.is_valid():
  try:
   with transaction.atomic():
    order=Order.objects.create(user=request.user,total=0,**form.cleaned_data)
    actual=Decimal('0')
    for row in rows:
     p=Product.objects.get(pk=row['product'].pk);q=row['quantity']
     if not Product.objects.filter(pk=p.pk,stock__gte=q).update(stock=F('stock')-q): raise ValueError(f'{p.name} has insufficient stock. Update your cart.')
     OrderItem.objects.create(order=order,product=p,name=p.name,price=p.price,quantity=q);actual+=p.price*q
    order.total=actual;order.save(update_fields=['total'])
   request.session['cart']={};messages.success(request,'Your order has been placed!');return redirect('order',pk=order.pk)
  except (ValueError,Product.DoesNotExist) as e: messages.error(request,str(e) or 'A product is no longer available.')
 return render(request,'checkout.html',{'form':form,'rows':rows,'total':total})
@login_required
def history(request): return render(request,'history.html',{'orders':Order.objects.filter(user=request.user).prefetch_related('items')})
@login_required
def order(request,pk): return render(request,'order.html',{'order':get_object_or_404(Order.objects.prefetch_related('items'),pk=pk,user=request.user)})
