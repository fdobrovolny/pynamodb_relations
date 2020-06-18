from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, Type, Union

from dateutil.tz import tzutc
from pynamodb.attributes import *
from pynamodb.constants import NUMBER
from pynamodb.models import Model


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


class TypeAttribute(StaticUnicodeAttribute):
    """
    Static field used to serve as identifier for record which Entity type this record is.
    """

    def __init__(
        self,
        static_value=None,
        hash_key=False,
        range_key=False,
        null=None,
        attr_name=None,
    ):
        super().__init__(
            static_value=static_value,
            hash_key=hash_key,
            range_key=range_key,
            null=null,
            attr_name=attr_name,
        )


class EnumAttributeMixin:
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


class UnicodeEnumAttribute(UnicodeAttribute, EnumAttributeMixin):
    pass


class NumberEnumAttribute(NumberAttribute, EnumAttributeMixin):
    pass
