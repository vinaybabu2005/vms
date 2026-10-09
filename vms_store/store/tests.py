from django.test import TestCase,Client,override_settings
from django.contrib.auth import get_user_model
from .models import Category,Product,Order
@override_settings(STORAGES={'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class StoreTests(TestCase):
 def setUp(self):
  self.user=get_user_model().objects.create_user('buyer',password='Buyer@12345')
  self.other=get_user_model().objects.create_user('other',password='Other@12345')
  self.p=Product.objects.create(name='Test mug',price=100,stock=2,category=Category.objects.create(name='Home'))
  self.data={'full_name':'Test Buyer','phone':'9876543210','address':'123 Sample Street, Guntur'}
 def add(self,p=None): self.client.post(f'/cart/add/{(p or self.p).pk}/')
 def test_checkout_and_history_isolation(self):
  self.client.force_login(self.user);self.add();r=self.client.post('/checkout/',self.data)
  self.assertEqual(r.status_code,302);self.p.refresh_from_db();self.assertEqual(self.p.stock,1)
  o=Order.objects.get();self.assertEqual(o.total,100);self.assertEqual(o.items.get().name,'Test mug');self.assertEqual(self.client.session['cart'],{})
  self.client.force_login(self.other);self.assertEqual(self.client.get(f'/orders/{o.pk}/').status_code,404)
 def test_checkout_atomic_stock_failure(self):
  self.client.force_login(self.user);self.add()
  p2=Product.objects.create(name='Lamp',price=200,stock=1,category=self.p.category);self.add(p2)
  p2.stock=0;p2.save();self.client.post('/checkout/',self.data)
  self.p.refresh_from_db();self.assertEqual(self.p.stock,2);self.assertEqual(Order.objects.count(),0)
 def test_stock_limit_and_remove(self):
  for _ in range(3): self.add()
  self.assertEqual(self.client.session['cart'][str(self.p.pk)],2)
  self.client.post(f'/cart/update/{self.p.pk}/',{'action':'remove'});self.assertEqual(self.client.session['cart'],{})
 def test_checkout_requires_login_and_post(self):
  self.add();self.assertEqual(self.client.get('/checkout/').status_code,302)
  self.assertEqual(self.client.get(f'/cart/add/{self.p.pk}/').status_code,405)
 def test_csrf(self):
  self.assertEqual(Client(enforce_csrf_checks=True).post(f'/cart/add/{self.p.pk}/').status_code,403)
 def test_pages_filters_and_invalid_delivery(self):
  for path in ['/','/cart/','/login/','/register/',f'/product/{self.p.pk}/','/?min=abc&max=NaN']:
   self.assertEqual(self.client.get(path).status_code,200)
  self.assertContains(self.client.get('/?q=Test&min=50&max=150'),'Test mug')
  self.client.force_login(self.user);self.add();self.client.post('/checkout/',{'full_name':'x','phone':'x','address':'x'});self.assertFalse(Order.objects.exists())


from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from .models import OrderItem
from .services import update_order,delete_order
from io import BytesIO
from PIL import Image
import tempfile

@override_settings(STORAGES={'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class DashboardTests(TestCase):
 def setUp(self):
  U=get_user_model()
  self.staff=U.objects.create_user('manager',password='Manager@12345',is_staff=True)
  self.customer=U.objects.create_user('shopper',password='Shopper@12345')
  self.other=U.objects.create_user('another',password='Another@12345')
  self.category=Category.objects.create(name='Home')
  self.product=Product.objects.create(name='Lamp',price=300,stock=8,category=self.category)
  self.order=Order.objects.create(user=self.customer,total=600,full_name='Shopper',phone='9876543210',address='Sample road, Guntur')
  OrderItem.objects.create(order=self.order,product=self.product,name='Lamp',price=300,quantity=2)
  self.data={'status':'placed','full_name':'Shopper','phone':'9876543210','address':'Sample road, Guntur','courier':'','tracking_number':'','tracking_url':'','shipping_notes':''}
 def test_staff_permission_all_routes(self):
  paths=['/dashboard/','/dashboard/orders/',f'/dashboard/orders/{self.order.pk}/',f'/dashboard/orders/{self.order.pk}/delete/','/dashboard/products/','/dashboard/products/add/',f'/dashboard/products/{self.product.pk}/edit/',f'/dashboard/products/{self.product.pk}/delete/','/dashboard/categories/',f'/dashboard/categories/{self.category.pk}/delete/','/dashboard/customers/',f'/dashboard/customers/{self.customer.pk}/']
  for path in paths: self.assertEqual(self.client.get(path).status_code,302)
  self.client.force_login(self.customer)
  for path in paths:
   self.assertEqual(self.client.get(path).status_code,403)
   self.assertEqual(self.client.post(path,{}).status_code,403)
  self.client.force_login(self.staff)
  for path in paths: self.assertEqual(self.client.get(path).status_code,200)
 def test_login_roles(self):
  self.client.post('/admin-login/',{'username':'shopper','password':'Shopper@12345'})
  self.assertNotIn('_auth_user_id',self.client.session)
  r=self.client.post('/admin-login/',{'username':'manager','password':'Manager@12345'})
  self.assertRedirects(r,'/dashboard/')
  self.client.logout()
  self.client.post('/login/',{'username':'manager','password':'Manager@12345'})
  self.assertNotIn('_auth_user_id',self.client.session)
  r=self.client.post('/login/',{'username':'shopper','password':'Shopper@12345'})
  self.assertRedirects(r,'/')
 def test_shipping_visible_only_to_owner(self):
  self.client.force_login(self.staff)
  data={**self.data,'status':'shipped','courier':'Demo Courier','tracking_number':'VMS123','tracking_url':'https://example.com/track','estimated_delivery':'2026-10-20','shipping_notes':'Your parcel is on the way.'}
  r=self.client.post(f'/dashboard/orders/{self.order.pk}/',data)
  self.assertEqual(r.status_code,302)
  self.client.force_login(self.customer)
  r=self.client.get(f'/orders/{self.order.pk}/');self.assertContains(r,'VMS123');self.assertContains(r,'Demo Courier')
  self.client.force_login(self.other);self.assertEqual(self.client.get(f'/orders/{self.order.pk}/').status_code,404)
 def test_cancel_once_and_delete_cancelled(self):
  self.client.force_login(self.staff)
  data={**self.data,'status':'cancelled','cancellation_reason':'other'}
  self.client.post(f'/dashboard/orders/{self.order.pk}/',data)
  self.product.refresh_from_db();self.assertEqual(self.product.stock,10)
  self.client.post(f'/dashboard/orders/{self.order.pk}/',data)
  self.product.refresh_from_db();self.assertEqual(self.product.stock,10)
  self.client.post(f'/dashboard/orders/{self.order.pk}/delete/')
  self.product.refresh_from_db();self.assertEqual(self.product.stock,10);self.assertFalse(Order.objects.exists())
 def test_address_lock_and_invalid_transitions(self):
  update_order(self.order.pk,{**self.data,'status':'shipped'})
  with self.assertRaises(ValueError): update_order(self.order.pk,{**self.data,'status':'shipped','address':'Different address'})
  with self.assertRaises(ValueError): update_order(self.order.pk,{**self.data,'status':'cancelled','cancellation_reason':'other'})
  update_order(self.order.pk,{**self.data,'status':'delivered'})
  self.order.refresh_from_db();self.assertEqual(self.order.status,'delivered')
 def test_delete_active_returns_stock_and_get_never_deletes(self):
  self.client.force_login(self.staff)
  self.client.get(f'/dashboard/orders/{self.order.pk}/delete/');self.assertTrue(Order.objects.exists())
  self.client.post(f'/dashboard/orders/{self.order.pk}/delete/');self.product.refresh_from_db();self.assertEqual(self.product.stock,10)
 def test_delete_shipped_never_restocks(self):
  update_order(self.order.pk,{**self.data,'status':'shipped'});delete_order(self.order.pk)
  self.product.refresh_from_db();self.assertEqual(self.product.stock,8)
 def test_product_upload_and_validation(self):
  self.client.force_login(self.staff);image=BytesIO();Image.new('RGB',(20,20),'green').save(image,format='PNG')
  with tempfile.TemporaryDirectory() as folder,override_settings(MEDIA_ROOT=folder):
   data={'name':'New mug','description':'Ceramic','price':'199','stock':'12','category':self.category.pk,'image':SimpleUploadedFile('mug.png',image.getvalue(),content_type='image/png')}
   self.assertEqual(self.client.post('/dashboard/products/add/',data).status_code,302)
   product=Product.objects.get(name='New mug');self.assertTrue(product.image)
   data['price']='-1';data.pop('image');self.client.post('/dashboard/products/add/',data)
   self.assertEqual(Product.objects.filter(name='New mug').count(),1)
 def test_unsafe_tracking_and_locked_form(self):
  self.client.force_login(self.staff)
  self.client.post(f'/dashboard/orders/{self.order.pk}/',{**self.data,'tracking_url':'javascript:alert(1)'})
  self.order.refresh_from_db();self.assertEqual(self.order.tracking_url,'')
  update_order(self.order.pk,{**self.data,'status':'shipped'})
  self.client.post(f'/dashboard/orders/{self.order.pk}/',{**self.data,'status':'shipped','address':'Tampered address'})
  self.order.refresh_from_db();self.assertEqual(self.order.address,'Sample road, Guntur')
 def test_category_protection_and_metrics(self):
  self.client.force_login(self.staff)
  self.client.post(f'/dashboard/categories/{self.category.pk}/delete/');self.assertTrue(Category.objects.exists())
  self.assertContains(self.client.get('/dashboard/'),'600.00')
  update_order(self.order.pk,{**self.data,'status':'cancelled','cancellation_reason':'other'})
  self.assertEqual(self.client.get('/dashboard/').context['revenue'],0)
 def test_mutation_csrf(self):
  c=Client(enforce_csrf_checks=True);c.force_login(self.staff)
  self.assertEqual(c.post(f'/dashboard/orders/{self.order.pk}/delete/').status_code,403)


class CustomerCancellationTests(TestCase):
 def setUp(self):
  U=get_user_model();self.customer=U.objects.create_user('cancelbuyer',password='Buyer@12345');self.other=U.objects.create_user('otherbuyer',password='Other@12345')
  self.category=Category.objects.create(name='Cancel test')
  self.product=Product.objects.create(name='Cancel product',price=50,stock=3,category=self.category)
  self.order=Order.objects.create(user=self.customer,total=100,full_name='Buyer',phone='9876543210',address='Sample address Guntur')
  OrderItem.objects.create(order=self.order,product=self.product,name='Cancel product',price=50,quantity=2)
 def test_get_does_not_cancel_and_reason_is_required(self):
  self.client.force_login(self.customer);self.client.get(f'/orders/{self.order.pk}/cancel/')
  self.order.refresh_from_db();self.assertEqual(self.order.status,'placed')
  r=self.client.post(f'/orders/{self.order.pk}/cancel/',{'reason':'','note':''})
  self.assertEqual(r.status_code,200);self.assertFalse(r.context['form'].is_valid());self.order.refresh_from_db();self.assertEqual(self.order.status,'placed')
 def test_customer_cancels_with_reason_once_and_sees_reason(self):
  self.client.force_login(self.customer)
  r=self.client.post(f'/orders/{self.order.pk}/cancel/',{'reason':'ordered_by_mistake','note':'I selected two by mistake.'})
  self.assertRedirects(r,f'/orders/{self.order.pk}/');self.order.refresh_from_db();self.product.refresh_from_db()
  self.assertEqual(self.order.status,'cancelled');self.assertEqual(self.order.cancellation_reason,'ordered_by_mistake');self.assertEqual(self.product.stock,5);self.assertTrue(self.order.cancelled_at)
  self.client.get(f'/orders/{self.order.pk}/cancel/');self.product.refresh_from_db();self.assertEqual(self.product.stock,5)
  self.assertContains(self.client.get(f'/orders/{self.order.pk}/'),'I selected two by mistake.')
 def test_other_user_cannot_cancel_order(self):
  self.client.force_login(self.other);self.assertEqual(self.client.get(f'/orders/{self.order.pk}/cancel/').status_code,404)
  self.client.post(f'/orders/{self.order.pk}/cancel/',{'reason':'other'});self.order.refresh_from_db();self.product.refresh_from_db();self.assertEqual(self.order.status,'placed');self.assertEqual(self.product.stock,3)
 def test_shipped_order_cannot_cancel(self):
  self.order.status='shipped';self.order.save();self.client.force_login(self.customer)
  self.assertRedirects(self.client.get(f'/orders/{self.order.pk}/cancel/'),f'/orders/{self.order.pk}/')
  self.client.post(f'/orders/{self.order.pk}/cancel/',{'reason':'other'});self.order.refresh_from_db();self.product.refresh_from_db();self.assertEqual(self.order.status,'shipped');self.assertEqual(self.product.stock,3)
 def test_customer_login_required(self):
  self.assertEqual(self.client.get(f'/orders/{self.order.pk}/cancel/').status_code,302)
 def test_admin_cancellation_requires_reason(self):
  staff=get_user_model().objects.create_user('cancelmanager',password='Manager@12345',is_staff=True)
  self.client.force_login(staff)
  data={'status':'cancelled','full_name':'Buyer','phone':'9876543210','address':'Sample address Guntur','courier':'','tracking_number':'','tracking_url':'','estimated_delivery':'','shipping_notes':'','cancellation_reason':'','cancellation_note':''}
  r=self.client.post(f'/dashboard/orders/{self.order.pk}/',data);self.assertEqual(r.status_code,200)
  self.order.refresh_from_db();self.product.refresh_from_db();self.assertEqual(self.order.status,'placed');self.assertEqual(self.product.stock,3)
