from inspect import getmembers
from typing import Type, Dict

from .base import RegisterDatabaseLink
from .models import Model


class BaseDatabase:
    ITEM_TYPE_MAPPING: Dict[str, Type[Model]] = {}

    @classmethod
    def from_raw(cls, item):
        return cls.ITEM_TYPE_MAPPING[item["type"]["S"]].from_raw_data(item)

    @classmethod
    def get_model(cls, name: str) -> Type[Model]:
        return cls.ITEM_TYPE_MAPPING[name]

    @classmethod
    def register_model(cls, name, model):
        cls.ITEM_TYPE_MAPPING[name] = model
        setattr(cls, name, model)

    @classmethod
    def register(cls, name):
        def f(model_cls):
            if name in cls.ITEM_TYPE_MAPPING:
                raise AttributeError(
                    f"Can't register '{model_cls.__name__}'. Model with name '{name}' already exists!"
                )

            cls.register_model(name, model_cls)

            for _, attribute in getmembers(
                model_cls, lambda o: issubclass(o.__class__, RegisterDatabaseLink)
            ):
                attribute._database = cls

            return model_cls

        return f
