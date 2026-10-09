import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
class Command(BaseCommand):
    help = 'Create/update the Render administrator from environment variables.'
    def handle(self,*args,**kwargs):
        password=os.environ.get('VMS_ADMIN_PASSWORD')
        if not password:
            self.stdout.write('No VMS_ADMIN_PASSWORD supplied; existing accounts left unchanged.')
            return
        username=os.environ.get('VMS_ADMIN_USERNAME','vms')
        try: validate_password(password,get_user_model()(username=username))
        except ValidationError as e: raise CommandError('Admin password does not meet password rules: '+ '; '.join(e.messages))
        user,_=get_user_model().objects.get_or_create(username=username)
        user.set_password(password)
        user.is_staff=user.is_superuser=user.is_active=True
        user.save()
        self.stdout.write(self.style.SUCCESS('Administrator account configured.'))
