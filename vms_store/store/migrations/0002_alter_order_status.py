from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [('store','0001_initial')]
    operations = [migrations.AlterField(model_name='order',name='status',field=models.CharField(max_length=20,default='placed',choices=[('placed','Placed'),('processing','Processing'),('shipped','Shipped'),('delivered','Delivered'),('cancelled','Cancelled')]))]
