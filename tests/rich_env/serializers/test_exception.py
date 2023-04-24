import traceback
from unittest import TestCase

from serialzy.api import StandardSchemaFormats
from serialzy.registry import DefaultSerializerRegistry
from serialzy.serializers.exception import ExceptionSerializer
from tests.rich_env.serializers.utils import serialize_and_deserialize


class ExceptionSerializationTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_exception_serialization(self):
        try:
            raise TypeError("test")
        except Exception as e:
            original_traceback = e.__traceback__
            serializer = self.registry.find_serializer_by_type(type(e))
            deserialized = serialize_and_deserialize(serializer, e)

        self.assertEqual(TypeError, type(deserialized[1]))
        self.assertEqual(("test", ), deserialized[1].args)
        current_traceback = traceback.extract_tb(deserialized[2])
        length = len(current_traceback)
        original_extracted = traceback.extract_tb(original_traceback)[-length:]
        self.assertEqual(original_extracted, current_traceback)

        self.assertFalse(serializer.stable())
        self.assertIn("tblib", serializer.meta())
        self.assertIn("tblib", serializer.requirements())

    def test_schema(self):
        try:
            raise TypeError("test")
        except Exception as e:
            serializer = self.registry.find_serializer_by_type(type(e))
            schema = serializer.schema(type(e))

        self.assertEqual(ExceptionSerializer.DATA_FORMAT, schema.data_format)
        self.assertEqual(StandardSchemaFormats.pickled_type.name, schema.schema_format)
        self.assertTrue(len(schema.schema_content) > 0)
        self.assertTrue('tblib' in schema.meta)
        self.assertTrue('cloudpickle' in schema.meta)

    def test_supported_types(self):
        serializer = self.registry.find_serializer_by_data_format(ExceptionSerializer.DATA_FORMAT)
        self.assertFalse(serializer.supported_types()(str))
        self.assertFalse(serializer.supported_types()(ExceptionSerializationTests))
        self.assertTrue(serializer.supported_types()(Exception))
        self.assertTrue(serializer.supported_types()(TypeError))
