from django.contrib import admin
from django.urls import path, re_path
from django.contrib.auth import views as auth
from django.conf import settings
from django.views.static import serve
from store import views as v
from store import dashboard as d
urlpatterns=[path('admin/',admin.site.urls),path('',v.home,name='home'),path('product/<int:pk>/',v.detail,name='detail'),path('cart/',v.cart,name='cart'),path('cart/add/<int:pk>/',v.add,name='add'),path('cart/update/<int:pk>/',v.update,name='update'),path('checkout/',v.checkout,name='checkout'),path('orders/',v.history,name='history'),path('orders/<int:pk>/',v.order,name='order'),path('orders/<int:pk>/cancel/',d.customer_cancel_order,name='customer_cancel_order'),path('register/',v.register,name='register'),path('login/',d.UserLogin.as_view(),name='login'),path('logout/',auth.LogoutView.as_view(),name='logout')]+[re_path(r'^media/(?P<path>.*)$', serve, {'document_root':settings.MEDIA_ROOT})]

urlpatterns += [
 path('admin-login/',d.AdminLogin.as_view(),name='admin_login'),
 path('dashboard/',d.overview,name='dashboard'),
 path('dashboard/orders/',d.orders,name='dashboard_orders'),
 path('dashboard/orders/<int:pk>/',d.order_detail,name='dashboard_order'),
 path('dashboard/orders/<int:pk>/delete/',d.order_delete,name='dashboard_order_delete'),
 path('dashboard/products/',d.products,name='dashboard_products'),
 path('dashboard/products/add/',d.product_edit,name='dashboard_product_add'),
 path('dashboard/products/<int:pk>/edit/',d.product_edit,name='dashboard_product_edit'),
 path('dashboard/products/<int:pk>/delete/',d.product_delete,name='dashboard_product_delete'),
 path('dashboard/categories/',d.categories,name='dashboard_categories'),
 path('dashboard/categories/<int:pk>/delete/',d.category_delete,name='dashboard_category_delete'),
 path('dashboard/customers/',d.customers,name='dashboard_customers'),
 path('dashboard/customers/<int:pk>/',d.customer,name='dashboard_customer'),
]
