from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Project-wide pagination defaults, applied to every list endpoint."""

    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 200
