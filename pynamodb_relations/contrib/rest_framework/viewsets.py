from rest_framework import mixins
from rest_framework.viewsets import ViewSetMixin

from pynamodb_relations.contrib.rest_framework import generics


class PynamoDBGenericViewSet(ViewSetMixin, generics.GenericPynamoDBAPIView):
    """
    The GenericViewSet class does not provide any actions by default,
    but does include the base set of generic view behavior, such as
    the `get_object` and `get_queryset` methods.
    """
    pass


class ReadOnlyPynamoDBModelViewSet(mixins.RetrieveModelMixin,
                                   mixins.ListModelMixin,
                                   PynamoDBGenericViewSet):
    """
    A viewset that provides default `list()` and `retrieve()` actions.
    """
    pass


class PynamoDBModelViewSet(mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin,
                           mixins.DestroyModelMixin,
                           mixins.ListModelMixin,
                           PynamoDBGenericViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass
