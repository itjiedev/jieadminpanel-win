import json
from django import forms
from email.policy import default
from jiefoundation.forms import FormBase

from .helper import  get_downloadsite


def download_sites():
    download_sites = get_downloadsite()
    sites = []
    for site in download_sites.values():
        sites.append((site['id'], site['site-name']))
    return sites


class InstallConfigForm(FormBase):
    install_folder = forms.CharField(
        label="安装目录",
        help_text="所有的版本都将统一安装到所选的目录中。建议使用空白文件夹~",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext':'请选择安装文件夹~'}
        )
    )
    install_source = forms.CharField(
        label="下载源",
        help_text="如果一直无法通过文件验证，请更换官方地址",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    check_file = forms.BooleanField(
        label="文件校验",
        help_text="如果多次文件校验不通过，可以尝试关闭后安装",
        widget=forms.CheckboxInput(attrs={'data-bootstrap-switch':'', 'data-on-color':'success' }),
        required=False, initial=False,
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['install_source'].widget.choices = download_sites()

class UninstallForm(FormBase):
    """
    Python卸载确认表单
    """
    accept = forms.BooleanField(
        label="确认卸载",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=True,
    )

class ImportForm(FormBase):
    """
    导入Python版本表单
    """
    import_dir = forms.CharField(
        label="Python所在目录",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext':'请选择导入的目录~'}
        )
    )


from .helper import get_versions
class PythonForm(FormBase):
    """
    安装Python版本表单
    """
    name = forms.CharField(
        label="环境标题",
        help_text='留空会自动以版本号作为标题',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        )
    )
    version = forms.CharField(
        label="Python版本",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'readonly':'True', 'lay-verify': 'required', 'lay-reqtext':'Python版本不能为空~'},
        )
    )
    folder = forms.CharField(
        label="安装路径",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'readonly':'True', 'lay-verify': 'required', 'lay-reqtext':'路径不能为空~'},
        )
    )
