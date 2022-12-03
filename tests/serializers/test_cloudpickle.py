import tempfile
from dataclasses import dataclass
from pickle import UnpicklingError
from unittest import TestCase

# noinspection PyPackageRequirements
import cloudpickle
from pure_protobuf.dataclasses_ import field, message
from pure_protobuf.types import int32

from serialzy.api import Schema, StandardDataFormats, StandardSchemaFormats
from serialzy.registry import DefaultSerializerRegistry
from tests.serializers.utils import serialize_and_deserialize


class CloudpickleSerializationTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_serializer(self):
        class B:
            def __init__(self, x: int):
                self.x = x

        serializer = self.registry.find_serializer_by_type(B)
        b = B(42)
        deserialized = serialize_and_deserialize(serializer, b)

        self.assertEqual(b.x, deserialized.x)
        self.assertFalse(serializer.stable())

    def test_schema(self):
        class B:
            def __init__(self, x: int):
                self.x = x

        serializer = self.registry.find_serializer_by_type(B)
        schema = serializer.schema(B)

        self.assertEqual(StandardDataFormats.pickle.name, schema.data_format)
        self.assertEqual(StandardSchemaFormats.pickled_type.name, schema.schema_format)
        self.assertTrue(len(schema.schema_content) > 0)
        self.assertIn("cloudpickle", serializer.meta())

    def test_resolve(self):
        class B:
            def __init__(self, x: int):
                self.x = x

        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.pickle.name)
        schema = serializer.schema(B)

        typ = serializer.resolve(schema)
        self.assertEqual(B.__module__, typ.__module__)
        self.assertEqual(B.__name__, typ.__name__)

        with self.assertRaisesRegex(ValueError, "Invalid data format*"):
            serializer.resolve(
                Schema(
                    StandardDataFormats.proto.name,
                    StandardSchemaFormats.pickled_type.name,
                    schema.schema_content,
                    {'cloudpickle': '0.0.0'}
                )
            )
        with self.assertRaisesRegex(ValueError, "Invalid schema format*"):
            serializer.resolve(
                Schema(
                    StandardDataFormats.pickle.name,
                    StandardSchemaFormats.json_pickled_type.name,
                    schema.schema_content,
                    {'cloudpickle': '0.0.0'}
                )
            )

        with self.assertRaises(UnpicklingError):
            serializer.resolve(
                Schema(StandardDataFormats.pickle.name, StandardSchemaFormats.pickled_type.name, 'data',
                       {'cloudpickle': '0.0.0'}))

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema(StandardDataFormats.pickle.name, StandardSchemaFormats.pickled_type.name, schema.schema_content,
                       {'cloudpickle': '10000.0.0'}))
            self.assertRegex(cm.output[0], 'WARNING:serialzy.base:Installed version of cloudpickle*')

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema(StandardDataFormats.pickle.name, StandardSchemaFormats.pickled_type.name, schema.schema_content))
            self.assertRegex(cm.output[0], 'WARNING:serialzy.base:No cloudpickle version in meta*')

    def test_unpickled_message_keeps_subclass(self):
        @message
        @dataclass
        class TestMessage:
            a: int32 = field(1, default=0)

        msg = TestMessage(42)
        pickled_msg_type = cloudpickle.dumps(type(msg))
        unpickled_msg_type = cloudpickle.loads(pickled_msg_type)

        with tempfile.TemporaryFile() as file:
            self.registry.find_serializer_by_type(type(msg)).serialize(msg, file)
            file.flush()
            file.seek(0)
            result = self.registry.find_serializer_by_type(
                unpickled_msg_type
            ).deserialize(file)

        self.assertEqual(msg.a, result.a)
