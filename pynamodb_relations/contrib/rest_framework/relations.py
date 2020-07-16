from pynamodb.attributes import Attribute
from rest_framework.relations import RelatedField


class UnicodeRelatedField(RelatedField):
    model_field: Attribute

    def __init__(self, **kwargs):
        self.model_field = kwargs.pop("model_field")
        super(UnicodeRelatedField, self).__init__(**kwargs)

    def to_representation(self, value):
        return self.model_field.serialize(value)

    def to_internal_value(self, data):
        return self.model_field.deserialize(data).get()
