from typing import Type

from pynamodb.attributes import Attribute
from pynamodb.indexes import Index
from pynamodb.models import Model


def get_or_None(model: Type[Model], *args, **kwargs):
    try:
        return model.get(*args, **kwargs)
    except model.DoesNotExist:
        return None


def _range_key_attribute(cls: Index) -> Attribute:
    """
    Returns the attribute class for the range key on Index.
    """
    # Use of deprecated method
    # https://github.com/pynamodb/PynamoDB/issues/793
    for attr_cls in cls._get_attributes().values():
        if attr_cls.is_range_key:
            return attr_cls
