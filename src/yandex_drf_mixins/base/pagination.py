from typing import Any

from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class LimitOffsetAllBaseMixin:
    all_query_param = "all"
    all_query_description = _("Retrieve all results at once")

    def get_schema_operation_parameters(self, view: Any) -> list[dict[str, Any]]:
        parameters = super().get_schema_operation_parameters(view)
        return parameters + [
            {
                "name": self.all_query_param,
                "required": False,
                "in": "query",
                "description": force_str(self.all_query_description),
                "schema": {"type": "boolean"},
            }
        ]

    def _need_to_show_all_items(self, request: Any) -> bool:
        value = request.query_params.get(self.all_query_param, False)
        return self._convert_to_boolean(value)

    @staticmethod
    def _convert_to_boolean(value: str | bool) -> bool:
        try:
            return serializers.BooleanField().to_internal_value(value)
        except serializers.ValidationError:
            return False


class BaseAPaginationMixin:
    async def aget_count(self, queryset: Any) -> int:
        try:
            return await queryset.acount()
        except (AttributeError, TypeError):
            return len(queryset)
