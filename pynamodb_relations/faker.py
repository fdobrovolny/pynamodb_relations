from factory import base


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
