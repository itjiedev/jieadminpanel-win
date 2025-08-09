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
        help_text="所有的版本都将经一安装到所选的目录中。建议使用空白文件夹~",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext':'请选择安装文件夹~'}
        )
    )
    install_source = forms.CharField(
        label="安装源",
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

class PackageInstallForm(FormBase):
    """
    Python包安装表单
    """
    package_name = forms.CharField(
        label="包名",
        widget=forms.TextInput(attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext':'请输入包名~'})
    )
    package_version = forms.CharField(
        label="版本",
        required=False,
        widget=forms.Select(
            attrs={'class': 'form-control'},
            choices=(('latest', '自动适配最新版本'),)
        ),
    )