from typing import Any, Callable, Optional, Type, Union, TYPE_CHECKING

from pynamodb.attributes import Attribute
from pynamodb.constants import STRING

from pynamodb_relations.base import RegisterDatabaseLink

if TYPE_CHECKING:
    from pynamodb_relations.models import Model


class ForwardRelation:
    pass


class ForwardManyToOneDescriptor:
    method: Callable
    value: Any
    _resolved: bool = False
    _model: Optional["Model"] = None
    _attribute: Attribute

    def __init__(
        self, method: Callable, value: Any, attribute: Attribute, model: "Model" = None
    ):
        self.method = method
        self.value = value
        self._attribute = attribute
        if model:
            self._model = model
            self._resolved = True

    def get(self) -> "Model":
        if self._resolved:
            return self._model
        self._model = self.method(self.value)
        self._resolved = True
        return self._model


class ForeignKeyAttribute(Attribute, RegisterDatabaseLink, ForwardRelation):
    attr_type = STRING
    related_model_attribute: str
    related_model_get_method: str
    related_model: Union[str, Type["Model"]]
    foreign_attribute: str

    def __init__(
        self,
        model: Union[str, Type["Model"]],
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
