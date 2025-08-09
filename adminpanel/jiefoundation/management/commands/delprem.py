from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '删除默认权限'

    def handle(self, *args, **options):
        app_list = {
            'admin': ['logentry'],
            'auth': ['permission', 'group'],
            'contenttypes': ['contenttype'],
            'sessions': ['session'],
            'captcha': ['captchastore'],
        }
        for app_label in app_list:
            for model_name in app_list[app_label]:
                Permission.objects.filter(
                    content_type=ContentType.objects.get(app_label=app_label, model=model_name)
                ).delete()
        self.stdout.write(self.style.SUCCESS('删除默认权限~'))