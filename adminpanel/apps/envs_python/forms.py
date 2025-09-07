from django import forms
from jiefoundation.forms import FormBase


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
            choices=(('latest', '自动适配版本'),)
        ),
    )

class PackagePipExportForm(FormBase):
    """
    Python包导出表单
    """
    save_path = forms.CharField(
        label="保存路径",
        widget=forms.TextInput(attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext':'请选择保存路径~'})
    )