from rest_framework import mixins
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet


class ReadCreateDeleteModelViewSet(mixins.CreateModelMixin,
                                   mixins.ListModelMixin,
                                   mixins.RetrieveModelMixin,
                                   mixins.DestroyModelMixin,
                                   GenericViewSet):

    http_method_names = ['get']
    permission_classes = (AllowAny,)
    pagination_class = None
