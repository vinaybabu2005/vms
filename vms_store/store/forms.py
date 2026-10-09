from django import forms
from django.core.validators import RegexValidator
class CheckoutForm(forms.Form):
 full_name=forms.CharField(max_length=120,label='Full name')
 phone=forms.CharField(max_length=15,validators=[RegexValidator(r'^\+?[0-9]{10,15}$','Enter a valid phone number (10–15 digits).')])
 address=forms.CharField(min_length=10,max_length=1000,widget=forms.Textarea(attrs={'rows':3}),label='Delivery address')

from django.contrib.auth.forms import AuthenticationForm
from .models import Product, Category, Order

class StaffAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise forms.ValidationError('This login is for administrators. Please use User Login.', code='not_staff')

class CustomerAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.is_staff:
            raise forms.ValidationError('Please use Admin Login for your staff account.', code='staff_account')

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name','description','category','price','stock','image']
        widgets = {'description':forms.Textarea(attrs={'rows':4})}
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'size') and image.size > 5*1024*1024:
            raise forms.ValidationError('Upload an image smaller than 5 MB.')
        return image

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class ShippingForm(forms.ModelForm):
    phone = forms.CharField(max_length=15,validators=[RegexValidator(r'^\+?[0-9]{10,15}$','Enter 10–15 digits.')])
    class Meta:
        model = Order
        fields = ['status','full_name','phone','address','courier','tracking_number','tracking_url','estimated_delivery','shipping_notes','cancellation_reason','cancellation_note']
        widgets = {'address':forms.Textarea(attrs={'rows':3}),'shipping_notes':forms.Textarea(attrs={'rows':3}),'estimated_delivery':forms.DateInput(attrs={'type':'date'},format='%Y-%m-%d')}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        from .services import TRANSITIONS
        allowed=TRANSITIONS.get(self.instance.status,set())
        self.fields['status'].choices=[(v,label) for v,label in Order.STATUS if v in allowed]
        if self.instance.status in ('shipped','delivered','cancelled'):
            for field in ('full_name','phone','address'):
                self.fields[field].disabled=True
    def clean_tracking_url(self):
        value=self.cleaned_data.get('tracking_url','')
        if value and not value.startswith(('https://','http://')):
            raise forms.ValidationError('Use an http or https tracking link.')
        return value


class CancellationForm(forms.Form):
    reason = forms.ChoiceField(choices=Order.CANCEL_REASONS, label='Why are you cancelling?')
    note = forms.CharField(required=False, max_length=500, label='Additional details (optional)', widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell us anything else we should know.'}))
