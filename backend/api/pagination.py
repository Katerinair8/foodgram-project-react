from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    page_size = settings.PAGE_SIZE
    page_size_query_param = 'limit'
