from typing import Any

from rest_framework.pagination import LimitOffsetPagination

from yandex_drf_mixins.base.pagination import LimitOffsetAllBaseMixin


class LimitOffsetAllPagination(LimitOffsetAllBaseMixin, LimitOffsetPagination):
    def paginate_queryset(self, queryset: Any, request: Any, view: Any = None) -> Any:
        if not self._need_to_show_all_items(request):
            return super().paginate_queryset(queryset, request, view)
        self.count = self.get_count(queryset)
        self.limit = self.count
        self.offset = self.get_offset(request)
        self.request = request
        if self.count == 0 or self.offset > self.count:
            return []
        return queryset[self.offset : self.offset + self.limit]
