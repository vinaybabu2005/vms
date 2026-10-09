from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from store.models import Category,Product
class Command(BaseCommand):
 help='Create demo users and products without resetting existing data.'
 def handle(self,*args,**kwargs):
  U=get_user_model()
  for username,password,staff in [('admin','Admin@1234',True),('vinay','Vinay@12345',False)]:
   if not U.objects.filter(username=username).exists(): U.objects.create_user(username,password=password,is_staff=staff,is_superuser=staff)
  data=[('Studio Headphones','Electronics',2499,'headphones','Comfortable wireless headphones for your daily playlist.'),('Everyday Backpack','Accessories',1299,'backpack','A spacious everyday backpack with room for all your essentials.'),('Ceramic Mug','Home',399,'mug','Your morning ritual, upgraded. Smooth ceramic with a comfortable handle.'),('Desk Lamp','Home',899,'lamp','Warm lighting for focused evenings and cozy corners.'),('Classic Notebook','Stationery',249,'notebook','Beautiful pages for your next big idea.'),('Smart Watch','Electronics',1999,'watch','A simple companion for time, activity and everyday style.')]
  for name,cat,price,image,description in data:
   c,_=Category.objects.get_or_create(name=cat)
   Product.objects.get_or_create(name=name,defaults={'category':c,'price':price,'stock':25,'image':f'products/{image}.png','description':description})
  self.stdout.write(self.style.SUCCESS('Demo ready. Admin: admin / Admin@1234 | User: vinay / Vinay@12345'))
