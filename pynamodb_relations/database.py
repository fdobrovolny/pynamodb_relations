from typing import Dict, Type

from .models import Model


class BaseDatabase:
    """
    This class holds links to other models(Entities) inside same database(table).
    """

    ITEM_TYPE_MAPPING: Dict[str, Type[Model]] = {}
    region: str
    table_name: str
    billing_mode: str

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
