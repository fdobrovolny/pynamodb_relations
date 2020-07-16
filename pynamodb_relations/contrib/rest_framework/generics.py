from rest_framework import generics as original_generics, mixins


class GenericPynamoDBAPIView(original_generics.GenericAPIView):
    pagination_class = None
    filter_backends = None

    def get_object(self):
        raise NotImplementedError("Please implement this yourself.")


# Concrete view classes that provide method handlers
# by composing the mixin classes with the base view.

class CreatePynamoDBAPIView(mixins.CreateModelMixin,
                            GenericPynamoDBAPIView):
    """
    Concrete view for creating a model instance.
    """

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ListPynamoDBAPIView(mixins.ListModelMixin,
                          GenericPynamoDBAPIView):
    """
    Concrete view for listing a queryset.
    """

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class RetrievePynamoDBAPIView(mixins.RetrieveModelMixin,
                              GenericPynamoDBAPIView):
    """
    Concrete view for retrieving a model instance.
    """

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class DestroyPynamoDBAPIView(mixins.DestroyModelMixin,
                             GenericPynamoDBAPIView):
    """
    Concrete view for deleting a model instance.
    """

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class UpdatePynamoDBAPIView(mixins.UpdateModelMixin,
                            GenericPynamoDBAPIView):
    """
    Concrete view for updating a model instance.
    """

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class ListCreatePynamoDBAPIView(mixins.ListModelMixin,
                                mixins.CreateModelMixin,
                                GenericPynamoDBAPIView):
    """
    Concrete view for listing a queryset or creating a model instance.
    """

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class RetrieveUpdatePynamoDBAPIView(mixins.RetrieveModelMixin,
                                    mixins.UpdateModelMixin,
                                    GenericPynamoDBAPIView):
    """
    Concrete view for retrieving, updating a model instance.
    """

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class RetrieveDestroyPynamoDBAPIView(mixins.RetrieveModelMixin,
                                     mixins.DestroyModelMixin,
                                     GenericPynamoDBAPIView):
    """
    Concrete view for retrieving or deleting a model instance.
    """

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class RetrieveUpdateDestroyPynamoDBAPIView(mixins.RetrieveModelMixin,
                                           mixins.UpdateModelMixin,
                                           mixins.DestroyModelMixin,
                                           GenericPynamoDBAPIView):
    """
    Concrete view for retrieving, updating or deleting a model instance.
    """

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
