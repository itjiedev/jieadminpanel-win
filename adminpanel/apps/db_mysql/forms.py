from django import forms

from jiefoundation.forms import FormBase
from mimetypes import init


class ConfigForm(FormBase):
    install_folder = forms.CharField(
        label='统一安装路径', required=True,
        help_text='多个版本Mysql将统一安装到这个文件夹路径中，安装时不再另外设置~',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext': '请选择安装文件夹~'}
        )
    )

class InitializeForm(FormBase):
    install_id = forms.CharField(widget=forms.HiddenInput)
    port = forms.IntegerField(
        label='端口', required=True,
        help_text='端口号不能冲突',
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext': '请输入端口号~'}
        )
    )
    set_service = forms.BooleanField(
        label='安装为windows服务', required=False,
        widget=forms.CheckboxInput(
            attrs={'lay-skin': "switch", 'title': "安装|不安装", 'lay-filter': "set_service"}
        )
    )
    service_auto = forms.BooleanField(
        label='服务自动启动', required=False,
        help_text='是否自动启动服务',
        widget=forms.CheckboxInput(
            attrs={'lay-skin': "switch", 'title': "自启动|手动"}
        )
    )
    service_name = forms.CharField(
        label='服务名称', required=False,
        help_text='请输入服务名称',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext': '请输入服务名称~'}
        )
    )


class UserPasswordForm(FormBase):
    password = forms.CharField(
        label='密码', required=True,
        help_text='请输入密码',
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext': '请输入密码~'}
        )
    )
    confirm_password = forms.CharField(
        label='确认密码', required=True,
        help_text='请输入确认密码',
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext': '请输入确认密码~'}
        )
    )
    def clean(self):
        clean_data = super(UserPasswordForm, self).clean()
        password = clean_data.get('password')
        confirm_password = clean_data.get('confirm_password')
        if password != confirm_password:
            self.add_error('confirm_password', '两次输入的密码不一致!')


class ConfigEditForm(FormBase):
    content = forms.CharField(
        label='配置内容', required=True,
        help_text='请输入配置内容',
        widget=forms.Textarea(
            attrs={
                'class': 'form-control bg-secondary',
                'spellcheck': 'false',  # 禁用拼写检查
                'autocomplete': 'off',  # 禁用自动完成
                'autocorrect': 'off',  # 禁用自动纠正
                'autocapitalize': 'off',
                'rows': 15, 'lay-verify': 'required', 'lay-reqtext': '请输入配置内容~'
            }
        )
    )

class ImportForm(FormBase):
    config_file = forms.CharField(
        label='配置文件', required=True,
        help_text='请选择导入 MySQL 的 my.ini 配置文件！不需要选择安装目录，会自动从配置文件中读取',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext': '请选择导入MySQL的my.ini配置文件~'}
        )
    )
    version = forms.CharField(required=False,widget=forms.HiddenInput())
    install_dir = forms.CharField(required=False,widget=forms.HiddenInput())
    data_dir = forms.CharField(required=False,widget=forms.HiddenInput())
    port = forms.CharField(required=False,widget=forms.HiddenInput())


class ImportServiceForm(FormBase):
    select_service_type = forms.CharField(required=True,)
    system_service_name = forms.CharField(required=False)
    service_name = forms.CharField(required=False)
    service_auto = forms.BooleanField(required=False)


class MysqlLoginForm(FormBase):
    username = forms.CharField(
        label='用户名', required=True,
        help_text='请输入用户名',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext': '请输入用户名~'}
        )
    )
    password = forms.CharField(
        label='密码', required=True,
        help_text='请输入密码',
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext': '请输入密码~'}
        )
    )
    port = forms.IntegerField(
        label='端口', required=True,
        help_text='请输入端口',
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'lay-verify': 'required|number', 'lay-reqtext': '请输入端口~'}
        )
    )

from .mysqlconn import MysqlConnectionManager

def get_character_sets(request, conn):
    character_sets = conn.get_character_sets()
    character_list = []
    for character_set in character_sets:
        character_list.append([character_set['charset_name'], character_set['charset_name']])
    return character_list

def get_collations(request, conn,  character_name):
    collations = conn.get_collations_by_charset(character_name)
    collation_list = []
    for collation in collations:
        collation_list.append([collation['collation_name'], collation['collation_name']])
    return collation_list


class MysqlDatabaseForm(FormBase):
    database_name = forms.CharField(
        label='数据库名称', required=True,
        help_text='请输入数据库名称',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext': '请输入数据库名称~'}
        )
    )
    # character_set = forms.CharField(
    #     label='字符集', required=True,
    #     help_text='请选择字符集',
    #     widget=forms.Select(
    #         attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext': '请选择字符集~', 'disabled': 'disabled'}
    #     )
    # )
    character_set = forms.CharField(
        label='字符集', required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext': '请输入字符集~', 'readonly': 'readonly'}
        )
    )
    collation = forms.CharField(
        label='排序规则', required=True,
        help_text='请选择排序规则',
        widget=forms.Select(
            attrs={'class': 'form-control', 'lay-verify': 'required', 'lay-reqtext': '请选择排序规则~'}
        )
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        mysql = MysqlConnectionManager(self.request)
        initial = self.initial
        self.fields['character_set'].widget.choices = get_character_sets(self.request, mysql)
        self.fields['collation'].widget.choices = get_collations(self.request, mysql, initial['character_set'])
        if 'database_name' in initial:
            self.fields['database_name'].widget.attrs['readonly'] = 'readonly'