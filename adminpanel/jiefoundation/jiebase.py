import json

from django.core.exceptions import  ValidationError
from django.utils.translation import ngettext
from django.utils.translation import gettext as _
from django.contrib.auth.password_validation import  MinimumLengthValidator, NumericPasswordValidator
from django.http import JsonResponse
from django.views import View
from django.core.exceptions import PermissionDenied, BadRequest


class JieMinimumLengthValidator(MinimumLengthValidator):

    def get_error_message(self):
        return ngettext(
            "Your password must contain at least %(min_length)d character.",
            "Your password must contain at least %(min_length)d characters.",
            self.min_length,
        ) % {"min_length": self.min_length}


class JieNumericPasswordValidator(NumericPasswordValidator):
    def validate(self, password, user=None):
        if password.isdigit():
            raise ValidationError(
                _("Your password can’t be entirely numeric."),
                code="password_entirely_numeric",
            )


class JsonView(View):
    """
    通用 JSON 响应视图基类
    """
    def render_to_json_response(self, context, status=200):
        """
        返回 JSON 响应
        """
        return JsonResponse(context, status=status)

    def render_to_json_success(self, message, status=200):
        """
        返回统一格式的成功响应
        """
        return self.render_to_json_response({
            'status': 'success',
            'message': message
        }, status=status)

    def render_to_json_error(self, message, status=400):
        """
        返回统一格式的错误响应
        """
        return self.render_to_json_response({
            'status': 'error',
            'message': message
        }, status=status)
