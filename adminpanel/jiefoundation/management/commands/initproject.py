import os
import shutil
import datetime
import random
from pathlib import Path

from django.conf import settings
from django.core.management import utils
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    rewrite_template_suffixes = (
        (".py-tpl", ".py"),
        (".txt-tpl", ".txt"),
        (".json-tpl", ".json"),
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('初始化项目结构'))
        base_dir = settings.BASE_DIR
        tmp_dir = base_dir / 'tmp'
        template_dir =  os.path.join(Path(__file__).resolve().parent.parent, 'project_template')

        # 如果项目里存在conf和 config 文件夹，提示并终止
        if os.path.exists(base_dir / 'conf') or os.path.exists(base_dir / 'config'):
            self.stdout.write(self.style.ERROR('项目已存在 conf 和 conf_d 文件夹，请勿重复初始化！'))
            return

        # shutil.rmtree(base_dir / 'conf_d', ignore_errors=True)
        # shutil.rmtree(base_dir / 'conf', ignore_errors=True)

        prefix_length = len(template_dir) + 1

        self.stdout.write(self.style.SUCCESS('复制新结构文件夹...'))
        for root, dirs, files in os.walk(template_dir):
            path_rest = root[prefix_length:]
            target_dir = os.path.join(base_dir, path_rest)
            os.makedirs(target_dir, exist_ok=True)

            for filename in files:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(base_dir, path_rest, filename)
                if filename.endswith((".pyo", ".pyc", ".py.class")):
                    continue
                for old_suffix, new_suffix in self.rewrite_template_suffixes:
                    if new_path.endswith(old_suffix):
                        new_path = new_path.removesuffix(old_suffix) + new_suffix
                        break
                with open(old_path, encoding="utf-8") as template_file:
                    content = template_file.read()
                with open(new_path, "w", encoding="utf-8") as new_file:
                    new_file.write(content)

        manage_file_path = base_dir / 'manage.py'
        settings_module = os.environ.get('DJANGO_SETTINGS_MODULE')
        settings_dir_name_old = settings_module.split('.')[0]
        settings_module_path = Path(base_dir / Path(settings_module.replace('.', '/')).parent)

        self.stdout.write(self.style.SUCCESS('备份原配置文件夹...'))
        now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        random_number = str(random.randint(100, 999))
        backup_dir_parent = base_dir / 'backup'
        if not backup_dir_parent.exists():
            os.mkdir(backup_dir_parent)
        backup_dir = backup_dir_parent / f"{now}-{random_number}"
        os.mkdir(backup_dir)
        shutil.copyfile(manage_file_path, backup_dir / 'manage.py')
        shutil.copytree(settings_module_path, backup_dir / settings_dir_name_old)

        self.stdout.write(self.style.SUCCESS('修改 manage.py 文件引用配置...'))
        with open(manage_file_path, 'r') as f:
            content = f.read()
            content = content.replace(
                f"'DJANGO_SETTINGS_MODULE', '{settings_dir_name_old}.settings'",
                "'DJANGO_SETTINGS_MODULE', 'conf.settings'"
            )
        with open(manage_file_path, 'w') as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS('删除原配置文件夹...'))
        shutil.rmtree(settings_module_path, ignore_errors=True)

        secret_key_file = base_dir / 'conf' / 'secret_key.py'
        new_secret_key = utils.get_random_secret_key()
        with open(secret_key_file, 'w', encoding='utf-8') as f:
            f.write(f"SECRET_KEY = 'django-insecure-{new_secret_key}'")

        self.stdout.write(self.style.SUCCESS('安装必须依赖项...'))
        os.system(f"pip install -r {base_dir / 'requirements.txt'}")

        self.stdout.write(self.style.SUCCESS('项目结构整理完成~'))