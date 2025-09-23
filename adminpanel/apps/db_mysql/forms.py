from django import forms

from jiefoundation.forms import FormBase


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