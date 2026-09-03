from typing import Any

from rest_framework.pagination import LimitOffsetPagination

from yandex_drf_mixins.base.pagination import BaseAPaginationMixin, LimitOffsetAllBaseMixin


class ALimitOffsetPagination(BaseAPaginationMixin, LimitOffsetPagination):
    async def apaginate_queryset(self, queryset: Any, request: Any, view: Any = None) -> Any:
        self.request = request
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None
        self.count = await self.aget_count(queryset)
        self.offset = self.get_offset(request)
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True
        if self.count == 0 or self.offset > self.count:
            return []
        return queryset[self.offset : self.offset + self.limit]


class ALimitOffsetAllPagination(BaseAPaginationMixin, LimitOffsetAllBaseMixin, LimitOffsetPagination):
    async def apaginate_queryset(self, queryset: Any, request: Any, view: Any = None) -> Any:
        self.request = request
        self.count = await self.aget_count(queryset)
        self.limit = self.count if self._need_to_show_all_items(request) else self.get_limit(request)
        if self.limit is None:
            return None
        self.offset = self.get_offset(request)
        if self.count == 0 or self.offset > self.count:
            return []
        return queryset[self.offset : self.offset + self.limit]
