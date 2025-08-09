import os
from pathlib import Path
from django.conf import settings
from django.core.management.templates import TemplateCommand
from django.core.management.base import CommandError


class Command(TemplateCommand):
    missing_args_message = "You must provide an application name."

    def handle(self, *args, **options):
        app_name = options.pop("name")
        target = options.pop("directory")
        if not target:
            target = os.path.join(settings.BASE_DIR, 'apps', app_name)
            try:
                os.makedirs(target)
            except FileExistsError:
                raise CommandError("The app folder %s  already exists. Please choose another app name。" % target)
            except OSError as e:
                raise CommandError(e)

        current_dir = Path(__file__).resolve().parent.parent.parent
        options['template'] = os.path.join(current_dir, 'management', 'app_template')
        super().handle("app", app_name, target, **options)
