import os
from django import forms
from jiefoundation.forms import FormBase
from .helper import get_pycharm_sdk

class PycharmInstallForm(FormBase):
    file_path = forms.CharField(
        label="选择 Pycharm 安装文件",
        help_text="选择你下载的安装包文件，确保是.exe格式的。",
        widget=forms.TextInput(attrs={'class': 'form-control','lay-verify': 'required', 'lay-reqtext': '请选择安装文件~'})
    )
    install_dir = forms.CharField(
        label="安装目标文件夹",
        widget=forms.TextInput(attrs={'class': 'form-control','lay-verify': 'required', 'lay-reqtext': '请选择要安装到的文件夹~'})

    )

class ProjectCreateForm(FormBase):
    project_dir = forms.CharField(
        label='项目文件夹',
        help_text='项目请不要使用路径中带有中文，空格等特殊字符的文件夹！',
        widget=forms.TextInput(attrs={'class': 'form-control','lay-verify': 'required', 'lay-reqtext': '请选择项目文件夹位置~'})
    )

def pycharm_sdk_choice():
    pycharm_sdk = get_pycharm_sdk()
    select_list = []
    for name, sdk in pycharm_sdk.items():
        path_exists_str = ''
        if not sdk['sdk_path_exists']:
            path_exists_str = '（路径异常）- '
        select_list.append((f'{sdk['sdk_name']}', f'{path_exists_str}{sdk['sdk_name']}（{sdk['sdk_path']}）'))
    return select_list

def get_python_sdk():
    from .helper import get_python_sdk
    sdk = get_python_sdk()
    select_list = []
    for install_dir, info in sdk.items():
        select_list.append((f'{install_dir}, {info['version']}', f'{info['name']}({info['version']})-({info['from'] } {install_dir})'))
    return select_list


class ProjectSetSdkForm(FormBase):
    project_path = forms.CharField(widget=forms.HiddenInput())
    sdk_type = forms.CharField(label='配置解释器方式')
    pycharm_sdk = forms.CharField(label='Pycharm已有配置', required=False, widget=forms.Select())
    python_sdk = forms.CharField(label='"运行环境"中的环境', required=False, widget=forms.Select())
    python_interpreter = forms.CharField(
        label="Python解释器文件", required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control'})
    )
    create_venv = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(
            attrs={'value': '1', 'title': '创建并使用venv虚拟环境', 'lay-filter': 'create_venv'}
        )
    )
    venv_path = forms.CharField(
        label='虚拟环境保存路径', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    delete_old_venv = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={'value': '1', 'title': '删除项目原虚拟环境文件夹(如果存在)'}
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pycharm_sdk'].widget.choices = pycharm_sdk_choice()
        self.fields['python_sdk'].widget.choices = get_python_sdk()


class PycharmResetForm(FormBase):
    confirm_reset = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'title': '确认重置'}),
    )