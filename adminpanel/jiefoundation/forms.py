from django import forms


class FormBase(forms.Form):
    """
    基础表单 不使用表单生成HTML5验证
    """
    use_required_attribute = False