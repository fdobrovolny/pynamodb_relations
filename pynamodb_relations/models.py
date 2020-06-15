from pynamodb.attributes import Attribute, MapAttribute
from pynamodb.connection.util import pythonic
from pynamodb.constants import ATTR_TYPE_MAP, ATTRIBUTES, NULL
from pynamodb.models import Model as PynamoModel
from pynamodb.types import HASH, RANGE

from .attributes import ProxiedAttributeMixin


class Model(PynamoModel):
    def _serialize(self, attr_map=False, null_check=True):
        """
        Serializes all model attributes for use with DynamoDB

        :param attr_map: If True, then attributes are returned
        :param null_check: If True, then attributes are checked for null
        """
        attributes = pythonic(ATTRIBUTES)
        attrs = {attributes: {}}
        for name, attr in self.get_attributes().items():
            value = getattr(self, name)
            if isinstance(attr, ProxiedAttributeMixin):
                value = attr.get_proxy_value(self, value)
            if isinstance(value, MapAttribute):
                if not value.validate():
                    raise ValueError(
                        "Attribute '{}' is not correctly typed".format(attr.attr_name)
                    )

            serialized = self._serialize_value(attr, value, null_check)
            if NULL in serialized:
                continue

            if attr_map:
                attrs[attributes][attr.attr_name] = serialized
            else:
                if attr.is_hash_key:
                    attrs[HASH] = serialized[ATTR_TYPE_MAP[attr.attr_type]]
                elif attr.is_range_key:
                    attrs[RANGE] = serialized[ATTR_TYPE_MAP[attr.attr_type]]
                else:
                    attrs[attributes][attr.attr_name] = serialized

        return attrs

    def _set_attributes(self, **attributes):
        """
        This function is called when a new object is initialized via __init__

        If some proxy value is based on value with default this will intialize it at model instance creation.
        """
        super()._set_attributes(**attributes)

        for name, attr in [
            (name, attr)
            for name, attr in self.get_attributes().items()
            if isinstance(attr, ProxiedAttributeMixin)
        ]:
            setattr(self, name, attr.get_proxy_value(self, getattr(self, name, None)))

    @classmethod
    def _serialize_keys(cls, hash_key, range_key=None):
        serialized_hash_key, serialized_range_key = super()._serialize_keys(
            hash_key, range_key
        )

        range_key_attr: Attribute = cls._range_key_attribute()
        if range_key_attr is not None and serialized_range_key is None:
            if isinstance(range_key_attr, ProxiedAttributeMixin):
                if range_key_attr.only_default:
                    return serialized_hash_key, range_key
                if range_key_attr.proxied_value_is_hash_key is True:
                    return serialized_hash_key, range_key_attr.serialize(hash_key)
                elif callable(range_key_attr.proxied_value):
                    return (
                        serialized_hash_key,
                        range_key_attr.proxied_value(hash_key, None, range_key_attr),
                    )

        return serialized_hash_key, serialized_range_key

    @classmethod
    def scan(cls,
             filter_condition=None,
             segment=None,
             total_segments=None,
             limit=None,
             last_evaluated_key=None,
             page_size=None,
             consistent_read=None,
             index_name=None,
             rate_limit=None,
             attributes_to_get=None):
        """
        Iterates through all items in the table

        :param filter_condition: Condition used to restrict the scan results
        :param segment: If set, then scans the segment
        :param total_segments: If set, then specifies total segments
        :param limit: Used to limit the number of results returned
        :param last_evaluated_key: If set, provides the starting point for scan.
        :param page_size: Page size of the scan to DynamoDB
        :param consistent_read: If True, a consistent read is performed
        :param index_name: If set, then this index is used
        :param rate_limit: If set then consumed capacity will be limited to this amount per second
        :param attributes_to_get: If set, specifies the properties to include in the projection expression
        """
        raise NotImplementedError("Scan is not yet implemented.")

    @classmethod
    def create_table(
            cls,
            wait=False,
            read_capacity_units=None,
            write_capacity_units=None,
            billing_mode=None,
            ignore_update_ttl_errors=False):
        """
        Create the table for this model

        :param wait: If set, then this call will block until the table is ready for use
        :param read_capacity_units: Sets the read capacity units for this table
        :param write_capacity_units: Sets the write capacity units for this table
        :param billing_mode: Sets the billing mode provisioned (default) or on_demand for this table
        """
        raise NotImplementedError(
            "Create table method on model is not possible. Please use `create_table` on Database.")

    @classmethod
    def delete_table(cls):
        """
        Delete the table for this model
        """
        raise NotImplementedError(
            "Delete table method on model is not possible. Please use `create_table` on Database.")

    @classmethod
    def dumps(cls):
        """
        Returns a JSON representation of this model's table
        """
        raise NotImplementedError(
            "Not implemented yet."
        )
