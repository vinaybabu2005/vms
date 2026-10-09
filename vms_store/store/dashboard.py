from functools import wraps
from datetime import timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Sum, Count, Q
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Product, Category, Order
from .forms import StaffAuthenticationForm, CustomerAuthenticationForm, ProductForm, CategoryForm, ShippingForm, CancellationForm
from .services import update_order, delete_order, cancel_customer_order

class AdminLogin(LoginView):
    template_name='admin_login.html'
    authentication_form=StaffAuthenticationForm
    def get_success_url(self): return '/dashboard/'

class UserLogin(LoginView):
    template_name='user_login.html'
    authentication_form=CustomerAuthenticationForm
    def get_success_url(self): return self.get_redirect_url() or '/'

def staff_only(view):
    @wraps(view)
    def wrapped(request,*args,**kwargs):
        if not request.user.is_authenticated:
            return redirect('/admin-login/?next='+request.path)
        if not request.user.is_active or not request.user.is_staff:
            return HttpResponseForbidden('Administrator access required. Use your customer account to shop.')
        return view(request,*args,**kwargs)
    return wrapped

def context(section,title,**kwargs):
    return {'section':section,'title':title,**kwargs}

def page(request, qs): return Paginator(qs,12).get_page(request.GET.get('page'))

@staff_only
def overview(request):
    orders=Order.objects.select_related('user')
    revenue=orders.exclude(status='cancelled').aggregate(v=Sum('total'))['v'] or Decimal('0')
    delivered=orders.filter(status='delivered').aggregate(v=Sum('total'))['v'] or Decimal('0')
    today=timezone.localdate(); bars=[]
    for i in range(6,-1,-1):
        day=today-timedelta(days=i)
        value=orders.filter(created_at__date=day).exclude(status='cancelled').aggregate(v=Sum('total'))['v'] or Decimal('0')
        bars.append({'label':day.strftime('%a'),'date':day.isoformat(),'value':value})
    maximum=max((x['value'] for x in bars),default=0) or 1
    for b in bars: b['height']=int(b['value']/maximum*100)
    counts=dict(orders.values('status').annotate(n=Count('id')).values_list('status','n'))
    statuses=[{'name':label,'count':counts.get(key,0),'key':key} for key,label in Order.STATUS]
    return render(request,'dashboard/overview.html',context('overview','Overview',revenue=revenue,delivered=delivered,order_count=orders.count(),product_count=Product.objects.count(),customer_count=get_user_model().objects.filter(is_staff=False).count(),pending_count=orders.filter(status__in=['placed','processing']).count(),recent=orders[:6],low_stock=Product.objects.filter(stock__lte=5).order_by('stock')[:5],bars=bars,statuses=statuses))

@staff_only
def orders(request):
    qs=Order.objects.select_related('user');q=request.GET.get('q','').strip();status=request.GET.get('status','')
    if q:
        match=Q(full_name__icontains=q)|Q(user__username__icontains=q)
        if q.isdigit(): match|=Q(pk=int(q))
        qs=qs.filter(match)
    if status in dict(Order.STATUS): qs=qs.filter(status=status)
    return render(request,'dashboard/orders.html',context('orders','Orders',page=page(request,qs),q=q,status=status,statuses=Order.STATUS))

@staff_only
def order_detail(request,pk):
    order=get_object_or_404(Order.objects.select_related('user').prefetch_related('items'),pk=pk)
    # Bind a separate instance: ModelForm validation mutates its instance.
    form=ShippingForm(request.POST or None,instance=Order.objects.get(pk=pk))
    if request.method=='POST' and form.is_valid():
        try:
            update_order(pk,form.cleaned_data)
            messages.success(request,'Order and shipping details updated. The customer can see these updates.')
            return redirect('dashboard_order',pk=pk)
        except ValueError as e: form.add_error(None,str(e))
    return render(request,'dashboard/order.html',context('orders',f'Order #{pk}',order=order,form=form))

@staff_only
def order_delete(request,pk):
    order=get_object_or_404(Order,pk=pk)
    if request.method=='POST':
        delete_order(pk);messages.success(request,'Order deleted.');return redirect('dashboard_orders')
    return render(request,'dashboard/confirm.html',context('orders','Delete order',object=order,back='/dashboard/orders/',explanation='This permanently removes the order and its items. Unshipped active orders return stock once; shipped or delivered orders do not return stock.'))

@staff_only
def products(request):
    qs=Product.objects.select_related('category').order_by('name');q=request.GET.get('q','').strip()
    if q: qs=qs.filter(name__icontains=q)
    return render(request,'dashboard/products.html',context('products','Products',page=page(request,qs),q=q))

@staff_only
def product_edit(request,pk=None):
    product=get_object_or_404(Product,pk=pk) if pk else None
    form=ProductForm(request.POST or None,request.FILES or None,instance=product)
    if request.method=='POST' and form.is_valid():
        form.save();messages.success(request,'Product saved.');return redirect('dashboard_products')
    return render(request,'dashboard/form.html',context('products','Edit product' if pk else 'Add product',form=form,back='/dashboard/products/',button='Save product'))

@staff_only
def product_delete(request,pk):
    product=get_object_or_404(Product,pk=pk)
    if request.method=='POST':
        product.delete();messages.success(request,'Product deleted. Existing orders keep their purchase details.');return redirect('dashboard_products')
    return render(request,'dashboard/confirm.html',context('products','Delete product',object=product,back='/dashboard/products/',explanation='The product will disappear from the store. Existing orders keep the purchased name and price.'))

@staff_only
def categories(request):
    form=CategoryForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        form.save();messages.success(request,'Category added.');return redirect('dashboard_categories')
    return render(request,'dashboard/categories.html',context('categories','Categories',form=form,categories=Category.objects.annotate(product_count=Count('product'))))

@staff_only
def category_delete(request,pk):
    category=get_object_or_404(Category,pk=pk)
    if request.method=='POST':
        try: category.delete();messages.success(request,'Category deleted.')
        except ProtectedError: messages.error(request,'Move or delete this category’s products before deleting it.')
        return redirect('dashboard_categories')
    return render(request,'dashboard/confirm.html',context('categories','Delete category',object=category,back='/dashboard/categories/',explanation='Only empty categories can be deleted.'))

@staff_only
def customers(request):
    qs=get_user_model().objects.filter(is_staff=False).annotate(order_count=Count('order')).order_by('-date_joined');q=request.GET.get('q','').strip()
    if q: qs=qs.filter(Q(username__icontains=q)|Q(email__icontains=q))
    return render(request,'dashboard/customers.html',context('customers','Customers',page=page(request,qs),q=q))

@staff_only
def customer(request,pk):
    user=get_object_or_404(get_user_model(),pk=pk,is_staff=False)
    orders=user.order_set.all()
    return render(request,'dashboard/customer.html',context('customers',user.username,customer=user,orders=orders,total=orders.exclude(status='cancelled').aggregate(v=Sum('total'))['v'] or 0))


@login_required
def customer_cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.status not in ('placed', 'processing'):
        messages.error(request, 'This order can no longer be cancelled. Contact the store if you need help.')
        return redirect('order', pk=order.pk)
    form = CancellationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            cancel_customer_order(order.pk, request.user, form.cleaned_data['reason'], form.cleaned_data['note'])
            messages.success(request, 'Your order was cancelled. The items have been returned to stock.')
            return redirect('order', pk=order.pk)
        except ValueError as e:
            form.add_error(None, str(e))
    return render(request, 'cancel_order.html', {'order': order, 'form': form})
