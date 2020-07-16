from pynamodb_relations.attributes import Attribute, EnumAttributeMixin, ProxiedAttributeMixin, UnicodeAttribute
from pynamodb_relations.contrib.rest_framework.model_meta import RelationInfo


def get_field_kwargs(field_name, model_field: Attribute):
    """
    Creates a default instance of a basic non-relational field.
    """
    kwargs = {}

    # The following will only be used by ModelField classes.
    # Gets removed for everything else.
    kwargs['model_field'] = model_field

    max_digits = getattr(model_field, 'max_digits', None)
    if max_digits is not None:
        kwargs['max_digits'] = max_digits

    if isinstance(model_field, ProxiedAttributeMixin):
        # If this field is read-only, then return early.
        # Further keyword arguments are not valid.
        kwargs['read_only'] = True
        return kwargs

    if model_field.default or model_field.null:
        kwargs['required'] = False

    if model_field.null:
        kwargs['allow_null'] = True

    if isinstance(model_field, EnumAttributeMixin):
        kwargs['choices'] = [(choice.value, choice.name) for choice in model_field.enum]

    return kwargs


def get_relation_kwargs(field_name, relation_info: RelationInfo):
    """
    Creates a default instance of a flat relational field.
    """
    model_field, related_model, to_many, reverse = relation_info
    kwargs = {
        # Relational field have to have a queryset but due to dynamodb nature we can't simply list all options
        'queryset': [],
        'model_field': model_field,
    }

    if to_many:
        kwargs['many'] = True

    if model_field:
        if model_field.default or model_field.default_for_new or model_field.null:
            kwargs['required'] = False
        if model_field.null:
            kwargs['allow_null'] = True
        if to_many and not model_field.null:
            kwargs['allow_empty'] = False

    return kwargs
