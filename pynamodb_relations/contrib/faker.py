import sys

try:
    from factory import base
except ImportError as e:
    print(
        "To use this integration you have to have factory installed. Try `pip install factory-boy`.",
        file=sys.stderr,
    )
    raise e


class PynamodbFactory(base.Factory):
    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Save Pynamodb instance.
        """
        instace = super()._create(model_class, *args, **kwargs)
        instace.save()
        return instace
