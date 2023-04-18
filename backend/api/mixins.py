from rest_framework import mixins, viewsets


class ListRetrieveViewSet(mixins.RetrieveModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    pass
