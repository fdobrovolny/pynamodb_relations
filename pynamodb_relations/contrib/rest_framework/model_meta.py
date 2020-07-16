"""
This file maps closely api of rest_framework.utils.models_meta
"""
from collections import namedtuple, OrderedDict
from typing import NamedTuple, Type

from pynamodb_relations import models
from pynamodb_relations.attributes import (Attribute, ProxiedUnicodeAttribute, StaticUnicodeAttribute)
from pynamodb_relations.forward_related import ForwardRelation
from pynamodb_relations.reverse_related import ReverseRelation

PrimaryKeyField = namedtuple(
    "PrimaryKeyField", ["name", "attribute"]
)

FieldInfo = namedtuple(
    "FieldResult",
    [
        "hk",  # Model field instance and name
        "rk",  # Model field instance and name
        "fields",  # Dict of field name -> model field instance
        "forward_relations",  # Dict of field name -> RelationInfo
        "reverse_relations",  # Dict of field name -> RelationInfo
        "fields_and_pk",  # Shortcut for 'hk' + 'rk' + 'fields'
        "relations",  # Shortcut for 'forward_relations' + 'reverse_relations'
    ],
)


class RelationInfo(NamedTuple):
    model_field: Attribute
    related_model: Type[models.Model]
    to_many: bool
    reverse: bool


def get_field_info(model: Type[models.Model]):
    hk = model._hash_key_attribute()
    hk_name = model._hash_keyname
    rk = model._range_key_attribute()
    rk_name = model._range_keyname
    fields = _get_fields(model)
    forward_relations = _get_forward_relationships(model)
    reverse_relations = _get_reverse_relationships(model)
    return FieldInfo(
        PrimaryKeyField(hk_name, hk), PrimaryKeyField(rk_name, rk), fields, forward_relations, reverse_relations,
        _merge_fields_and_pk(hk, hk_name, rk, rk_name, fields),
        _merge_relationships(forward_relations, reverse_relations)
    )


def _get_fields(model: Type[models.Model]):
    fields = OrderedDict()
    for name, attribute in model.get_attributes().items():
        if (
            not name.startswith("_")
            and name != model._version_attribute_name
            and name != model._type_attribute_name
            and not isinstance(attribute, StaticUnicodeAttribute)
            and not isinstance(attribute, ProxiedUnicodeAttribute)
            and not isinstance(attribute, ForwardRelation)
            and not isinstance(attribute, ReverseRelation)
        ):
            fields[name] = attribute

    return fields


def _get_forward_relationships(model: Type[models.Model]):
    fields = OrderedDict()
    for name, attribute in model.get_forward_relations().items():
        fields[name] = RelationInfo(
            attribute, attribute.get_related_model(), to_many=False, reverse=False
        )

    return fields


def _get_reverse_relationships(model: Type[models.Model]):
    fields = OrderedDict()
    for name, attribute in model.get_reverse_relations().items():
        fields[name] = RelationInfo(
            attribute, attribute.get_related_model(), to_many=True, reverse=True
        )

    return fields


def _merge_fields_and_pk(hk, hk_name, rk, rk_name, fields):
    fields_and_pk = OrderedDict()
    fields_and_pk['sk'] = rk
    fields_and_pk[rk_name] = rk
    fields_and_pk['hk'] = hk
    fields_and_pk[hk_name] = hk
    fields_and_pk.update(fields)

    return fields_and_pk


def _merge_relationships(forward_relations, reverse_relations):
    return OrderedDict(
        list(forward_relations.items()) +
        list(reverse_relations.items())
    )
