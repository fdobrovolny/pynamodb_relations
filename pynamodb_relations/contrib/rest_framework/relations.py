from pynamodb.attributes import Attribute
from rest_framework.fields import get_attribute
from rest_framework.relations import RelatedField

from pynamodb_relations.models import Model


class UnicodeRelatedField(RelatedField):
    """
    This field serves as Proxy between Unicode Related field and DRF.

    Attributes:
        disable_related_object_resolve: If False object is obtained
            from the DynamoDB. If True only it's id is used without
            checking if the object does still exist.

    """
    model_field: Attribute
    disable_related_object_resolve: bool = True

    def __init__(self, **kwargs):
        self.model_field = kwargs.pop("model_field")
        self.disable_related_object_resolve = kwargs.pop(
            "disable_related_object_resolve",
            self.disable_related_object_resolve
        )
        super(UnicodeRelatedField, self).__init__(**kwargs)

    def to_representation(self, value):
        return self.model_field.serialize(value)

    def to_internal_value(self, data):
        return self.model_field.deserialize(data).get()

    def get_attribute(self, instance: Model):
        if self.disable_related_object_resolve:
            attribute_instance: Model = get_attribute(instance, self.source_attrs[:-1])
            if attribute_instance.attribute_values[self.source_attrs[-1]]._resolved is False:
                return instance.attribute_values[self.source_attrs[-1]].value

        return super().get_attribute(instance)
