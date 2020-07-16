import unittest

from rest_framework.fields import BooleanField, CharField, DateTimeField, IntegerField, ListField, DictField

from pynamodb_relations import attributes
from pynamodb_relations.contrib.rest_framework.serializers import PynamoModelSerializer
from pynamodb_relations.database import BaseDatabase
from pynamodb_relations.models import Model


class PynamoDBRelationsSerializerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class TestDatabase(BaseDatabase):
            table_name = "Test"

        cls.database = TestDatabase

        class Thread(Model):
            class Meta:
                name = 'Thread'
                database = TestDatabase

            forum_name = attributes.UnicodeAttribute(hash_key=True)
            subject = attributes.UnicodeAttribute(range_key=True)
            views = attributes.NumberAttribute(default=0)
            replies = attributes.NumberAttribute(default=0)
            answered = attributes.NumberAttribute(default=0)
            last_post_datetime = attributes.UTCDateTimeAttribute()
            locked = attributes.BooleanAttribute(default=False)
            tags = attributes.ListAttribute()
            dict = attributes.MapAttribute()

        cls.model = Thread

    def test_serializer_standard_fields_mapping(self):
        class ThreadSerializer(PynamoModelSerializer):
            class Meta:
                model = self.database.Thread
                fields = "__all__"

        serializer = ThreadSerializer()
        self.assertEqual([
            'forum_name', 'subject',
            'answered', 'dict', 'last_post_datetime',
            'locked', 'replies', 'tags', 'views',
        ], list(serializer.fields.keys()))
        self.assertTrue(isinstance(serializer.fields["forum_name"], CharField))
        self.assertTrue(isinstance(serializer.fields["subject"], CharField))
        self.assertTrue(isinstance(serializer.fields["answered"], IntegerField))
        self.assertTrue(isinstance(serializer.fields["last_post_datetime"], DateTimeField))
        self.assertTrue(isinstance(serializer.fields["replies"], IntegerField))
        self.assertTrue(isinstance(serializer.fields["views"], IntegerField))
        self.assertTrue(isinstance(serializer.fields["tags"], ListField))
        self.assertTrue(isinstance(serializer.fields["dict"], DictField))
        self.assertTrue(isinstance(serializer.fields["locked"], BooleanField))


if __name__ == '__main__':
    unittest.main()
