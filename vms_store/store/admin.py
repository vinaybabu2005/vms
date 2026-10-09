from django.contrib import admin
from .models import Category,Product,Order,OrderItem
admin.site.site_header='V.M.S Store Administration'
admin.site.site_title='V.M.S Admin'
admin.site.register(Category)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
 list_display=['name','category','price','stock']
 list_filter=['category']
 search_fields=['name']
class ItemInline(admin.TabularInline):
 model=OrderItem
 extra=0
 can_delete=False
 readonly_fields=['product','name','price','quantity']
 def has_add_permission(self,request,obj=None): return False
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
 list_display=['id','user','total','status','created_at']
 list_filter=['status','created_at']
 search_fields=['user__username','full_name']
 readonly_fields=['user','total','created_at','full_name','phone','address','payment_method','status','courier','tracking_number','tracking_url','estimated_delivery','shipping_notes','stock_restored']
 inlines=[ItemInline]
 def has_add_permission(self,request): return False
 def has_delete_permission(self, request, obj=None):
    return False

# Order cancellation and deletion run through the dashboard to keep stock consistent.
