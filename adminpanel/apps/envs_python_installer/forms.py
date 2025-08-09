import json
from django import forms
from jiefoundation.forms import FormBase


def choice_python_list():
    from .config import installed_file_path, python_version_file_path
    installed_python =  []
    choice_python = []
    with open(installed_file_path, 'r', encoding='utf-8') as f:
        installed_file_path = json.load(f)
        for version, info in installed_file_path.items():
            installed_python.append(version)

    with open(python_version_file_path, 'r', encoding='utf-8') as f:
        python_versions = json.load(f)
        for version, version_info in python_versions.items():
            if version not in installed_python:
                choice_python.append(
                    (version, version_info['display-name'])
                )
    return choice_python


def choice_download_source():
    from .config import python_download_path

    choice_download = []
    with open(python_download_path, 'r', encoding='utf-8') as f:
        python_sources = json.load(f)
        for source in python_sources:
            choice_download.append((source['id'], source['site-name']))
    return choice_download


class PythonInstallForm(FormBase):
    """
    Python安装表单
    """
    folder = forms.CharField(
        label="安装目录",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['version'] = forms.ChoiceField(
            label="Python版本",
            choices=choice_python_list(),
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        self.fields['download_source'] = forms.ChoiceField(
            label="下载镜像源",
            choices=choice_download_source(),
            widget=forms.Select(attrs={'class': 'form-control'})
        )


class PythonUninstallForm(FormBase):
    """
    Python卸载确认表单
    """
    rm_folder =  forms.BooleanField(
        label="卸载后删除安装目录",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False,
    )
    accept = forms.BooleanField(
        label="确认卸载",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=True,
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