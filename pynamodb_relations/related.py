from typing import Any, Optional, Type, Union

from pynamodb.indexes import Index
from pynamodb.models import Model
from pynamodb.pagination import ResultIterator

from . import attributes
from .base import RegisterDatabaseLink
from .utils import _range_key_attribute


class Relation:
    pass


class ForeignKeyRelationManager:
    hash_key: Any
    related: Union[Type[Model], Type[Index]]

    def __init__(self, related: Union[Type[Model], Type[Index]], hash_key):
        self.related = related
        self.hash_key = hash_key

    def get(self, *args, **kwargs) -> Model:
        """
        Returns a single object using the provided keys

        Args:
            *args: See Model.get for more info on arguments.
            **kwargs: See Model.get for more info on arguments.

        Returns:
            Instance

        Raises:
            related.DoesNotExist(DoesNotExist) - When no matching instance was found
        """
        return self.related.get(self.hash_key, *args, **kwargs)

    def query(self, range_key_condition=None, *args, **kwargs) -> ResultIterator:
        """
        Provides a high level query API

        Args:
            range_key_condition: Condition for range key if not specified we try to guess what it should be
            *args: See Model.query for more info on arguments.
            **kwargs: See Model.query for more info on arguments.

        Returns:
            ResultIterator

        Raises:
            ValueError - range_key_condition is None and can not be guessed.

        Range key condition guessing:
            If range key on related model is:
            * PrefixedUnicodeAttribute - we use the prefix to filter by it.
            * StaticUnicodeAttribute - we use it's static value to filter by it.
        """
        if range_key_condition is None:
            if isinstance(self.related, Index):
                range_key_attribute = _range_key_attribute(self.related)
            else:
                range_key_attribute = self.related.get_attributes()[
                    self.related._range_keyname
                ]
            if isinstance(range_key_attribute, attributes.PrefixedUnicodeAttribute):
                range_key_condition = range_key_attribute.startswith("")
            elif isinstance(range_key_attribute, attributes.StaticUnicodeAttribute):
                range_key_condition = (
                        range_key_attribute == range_key_attribute.static_value
                )
            else:
                raise ValueError(
                    "ForeignKeyRelationManager can not do query as related model's range key can not "
                    "be automatically guessed and range_key_condition was not specified."
                )
        return self.related.query(self.hash_key, range_key_condition, *args, **kwargs)

    def count(self, range_key_condition=None, *args, **kwargs) -> int:
        """
        Provides a filtered count

        Args:
            range_key_condition: Condition for range key if not specified we try to guess what it should be
            *args: See Model.count for more info on arguments.
            **kwargs: See Model.count for more info on arguments.

        Returns:
            Number of related elements.

        Raises:
            ValueError - range_key_condition is None and can not be guessed.

        Range key condition guessing:
            If range key on related model is:
            * PrefixedUnicodeAttribute - we use the prefix to filter by it.
            * StaticUnicodeAttribute - we use it's static value to filter by it.
        """
        if range_key_condition is None:
            sort_key_attribute = self.related.get_attributes()[
                self.related._range_keyname
            ]
            if isinstance(sort_key_attribute, attributes.PrefixedUnicodeAttribute):
                range_key_condition = sort_key_attribute.startswith("")
            elif isinstance(sort_key_attribute, attributes.StaticUnicodeAttribute):
                range_key_condition = (
                        sort_key_attribute == sort_key_attribute.static_value
                )
            else:
                raise ValueError(
                    "ForeignKeyRelationManager can not do count as related model's range key can not "
                    "be automatically guessed and range_key_condition was not specified."
                )
        return self.related.count(self.hash_key, range_key_condition, *args, **kwargs)


class PrimaryKeyReverseForeignKeyRelation(Relation, RegisterDatabaseLink):
    """
    Reverse relation for item with FK to this object with same hash key using composite PK.
    """

    related_model: Union[str, Type[Model]]
    index: Optional[str] = None

    def __init__(self, model: Union[str, Type[Model]], index: Optional[str] = None):
        self.related_model = model
        self.index = index

    def get_related_model(self):
        if isinstance(self.related_model, str):
            if self._database is None:
                raise AssertionError(
                    "PrimaryKeyReverseForeignKeyRelation have model name supplied but was not hooked"
                    "up to the registry by BaseDatabase.register."
                )
            self.related_model = self._database.get_model(self.related_model)

        return self.related_model

    def __get__(self, instance: Union[Model], owner):
        if instance is None:
            return self

        if self.index:
            instance._get_indexes()
            dynamo_attr_name = (
                instance._index_classes[self.index]._hash_key_attribute().attr_name
            )
            python_attr_name = instance._dynamo_to_python_attr(dynamo_attr_name)
            return ForeignKeyRelationManager(
                related=self.get_related_model()._index_classes[self.index],
                hash_key=getattr(instance, python_attr_name),
            )

        return ForeignKeyRelationManager(
            related=self.get_related_model(),
            hash_key=getattr(instance, instance._hash_keyname),
        )
