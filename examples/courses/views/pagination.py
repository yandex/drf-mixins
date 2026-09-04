from rest_framework.pagination import LimitOffsetPagination


class IntrasearchPaginator(LimitOffsetPagination):
    """
    Actual pagination happens in the external API during search, so this paginator
    does not modify the queryset. It only adds pagination fields to the response.
    """

    def paginate_queryset(self, queryset, request, count):
        self.limit = self.get_limit(request)
        self.offset = self.get_offset(request)
        self.request = request
        self.count = count

        if self.limit is None:
            return None

        self.display_page_controls = self.count > self.limit

        return list(queryset)
