from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, Type, Union

from dateutil.tz import tzutc
from pynamodb.attributes import *
from pynamodb.constants import NUMBER, STRING
from pynamodb.models import Model

from .base import RegisterDatabaseLink


class ForwardManyToOneDescriptor:
    method: Callable
    value: Any
    _resolved: bool = False
    _model: Optional[Model] = None
    _attribute: Attribute

    def __init__(
        self, method: Callable, value: Any, attribute: Attribute, model: Model = None
    ):
        self.method = method
        self.value = value
        self._attribute = attribute
        if model:
            self._model = model
            self._resolved = True

    def get(self) -> Model:
        if self._resolved:
            return self._model
        self._model = self.method(self.value)
        self._resolved = True
        return self._model


class ForeignKeyAttribute(Attribute, RegisterDatabaseLink):
    attr_type = STRING
    related_model_attribute: str
    related_model_get_method: str
    related_model: Union[str, Type[Model]]
    foreign_attribute: str

    def __init__(
        self,
        model: Union[str, Type[Model]],
        *args,
        attribute: str = "uuid",
        get_method: Optional[str] = None,
        **kwargs,
    ):
        self.related_model = model
        self.related_model_attribute = attribute
        self.related_model_get_method = get_method or f"get_by_{attribute}"

        super().__init__(*args, **kwargs)

    def get_related_model(self):
        if isinstance(self.related_model, str):
            if self._database is None:
                raise AssertionError(
                    "ForeignKeyAttribute have model name supplied but was not hooked"
                    "up to the registry by BaseDatabase.register."
                )
            self.related_model = self._database.get_model(self.related_model)

        return self.related_model

    def serialize(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        elif isinstance(value, str):
            return value
        elif isinstance(value, self.get_related_model()):
            attr_value = getattr(value, self.related_model_attribute)
            attr = value.get_attributes()[self.related_model_attribute]
            return attr.serialize(attr_value)
        elif isinstance(value, ForwardManyToOneDescriptor):
            return (
                self.get_related_model()
                .get_attributes()[self.related_model_attribute]
                .serialize(value.value)
            )
        else:
            raise ValueError(
                f"Can't serialize unrecognized type {type(value)} for {self.__class__.__name__}."
            )

    def deserialize(self, value: Any) -> Optional[ForwardManyToOneDescriptor]:
        if value is None:
            return None

        return ForwardManyToOneDescriptor(**self.construct_descriptor_kwargs(value))

    def construct_descriptor_kwargs(self, value, model=None):
        return dict(
            method=getattr(self.get_related_model(), self.related_model_get_method),
            value=value,
            attribute=self,
            model=model,
        )

    def __set__(self, instance, value):
        if instance:
            if isinstance(value, str):
                attr_name = instance._dynamo_to_python_attrs.get(
                    self.attr_name, self.attr_name
                )
                instance.attribute_values[attr_name] = ForwardManyToOneDescriptor(
                    **self.construct_descriptor_kwargs(value)
                )
            elif not isinstance(value, self.get_related_model()) and not isinstance(
                value, ForwardManyToOneDescriptor
            ):
                raise ValueError(
                    'Cannot assign "%r": "%s.%s" must be a "%s" instance.'
                    % (
                        value,
                        instance.__class__.__name__,
                        self.attr_name,
                        self.get_related_model().__name__,
                    )
                )
            elif isinstance(value, self.get_related_model()):
                attr_name = instance._dynamo_to_python_attrs.get(
                    self.attr_name, self.attr_name
                )
                if attr_name in instance.attribute_values:
                    instance.attribute_values[attr_name].value = getattr(
                        value, self.related_model_attribute
                    )
                    instance.attribute_values[attr_name]._model = value
                else:
                    instance.attribute_values[attr_name] = ForwardManyToOneDescriptor(
                        **self.construct_descriptor_kwargs(
                            getattr(value, self.related_model_attribute), value
                        )
                    )
            else:
                super().__set__(instance, value)

    def __get__(self, instance, owner):
        x = super().__get__(instance, owner)
        if isinstance(x, ForwardManyToOneDescriptor):
            return x.get()
        return x


class ProxiedAttributeMixin:
    """
    Attribute Mixin to be able to base this field value based on another field.

    Attributes:
        proxied_value - name of attribute you want to use it's value or
                        callable which gets ModelInstance (during get() if this attribute
                        is range_key ModelInstance is None), current value
                        if any exists and this attribute instance.
        only_default - Use proxied value only if current value is None. Default False
        proxied_value_is_hash_key - In case this attribute is range_key if True and call
                                    will not have range key specified setting this to true
                                    will automatically calculate it's value
    """

    proxied_value: Union[
        str, Callable[[Any, Optional[Model], "ProxiedAttributeMixin"], Any], None
    ]
    proxied_value_is_hash_key: bool = False
    only_default: bool = False

    def __init__(
        self,
        *args,
        proxied_value=None,
        only_default=False,
        proxied_value_is_hash_key=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if proxied_value_is_hash_key is False and proxied_value is None:
            raise ValueError(
                "proxied_value can not be null if proxied_value_is_hash_key is False."
            )
        self.proxied_value = proxied_value
        self.only_default = only_default
        self.proxied_value_is_hash_key = proxied_value_is_hash_key

    def get_proxy_value(self, obj: Model, value=None):
        if self.only_default and value is not None:
            return value
        if self.proxied_value is None and self.proxied_value_is_hash_key:
            return obj.get_attributes()[self.proxied_value].serialize(
                getattr(obj, obj._hash_keyname)
            )
        if callable(self.proxied_value):
            return self.proxied_value(value, obj, self)
        return obj.get_attributes()[self.proxied_value].serialize(
            getattr(obj, self.proxied_value)
        )


class ProxiedUnicodeAttribute(UnicodeAttribute, ProxiedAttributeMixin):
    pass


class PrefixedUnicodeAttribute(UnicodeAttribute):
    """
    Unicode Attribute with static prefix.
    """

    prefix: str = None

    def __init__(self, prefix, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefix = prefix

    def serialize(self, value):
        if value is not None:
            return self.prefix + (super().serialize(value) if value != "" else value)
        return value

    def deserialize(self, value):
        if value is None:
            return value
        elif value.startswith(self.prefix):
            return value[len(self.prefix) :]
        else:
            raise AttributeError(
                f"Prefix {self.prefix} was not found during deserialization in value '{str(value)}'"
            )


class ProxiedPrefixedUnicodeAttribute(ProxiedAttributeMixin, PrefixedUnicodeAttribute):
    pass


class UnixTimestampAttribute(Attribute):
    """
    Attribute for storing time as unix timestamp.
    """

    attr_type = NUMBER

    def serialize(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=tzutc())
        return str(int(value.astimezone(tzutc()).timestamp()))

    def deserialize(self, value: Union[int, str, float]) -> datetime:
        return datetime.utcfromtimestamp(int(value)).replace(tzinfo=tzutc())


class StaticUnicodeAttribute(UnicodeAttribute):
    """
    Static attribute
    """

    static_value: str

    def __init__(
        self, static_value, hash_key=False, range_key=False, null=None, attr_name=None,
    ):
        super().__init__(
            hash_key=hash_key,
            range_key=range_key,
            null=null,
            default=static_value,
            default_for_new=None,
            attr_name=attr_name,
        )
        self.static_value = static_value

    def serialize(self, value: str) -> str:
        if value != self.static_value:
            raise ValueError(
                f"Static value {self.static_value} does not match '{value}'."
            )

        return super().serialize(self.static_value)

    def deserialize(self, value: str) -> str:
        if value != self.static_value:
            raise ValueError(
                f"Static value {self.static_value} does not match '{value}'."
            )

        return super().deserialize(self.static_value)


class EnumFieldMixin:
    enum: Type[Enum]

    def __init__(
        self,
        enum: Type[Enum],
        hash_key=False,
        range_key=False,
        null=None,
        default=None,
        default_for_new=None,
        attr_name=None,
    ):
        super().__init__(hash_key, range_key, null, default, default_for_new, attr_name)
        self.enum = enum

    def serialize(self, value: [str, Enum]) -> Enum:
        return self.enum(value)

    def deserialize(self, value: Enum) -> str:
        return value.value


class UnicodeEnumField(UnicodeAttribute, EnumFieldMixin):
    pass


class NumberEnumField(NumberAttribute, EnumFieldMixin):
    pass
