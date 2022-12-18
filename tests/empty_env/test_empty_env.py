from typing import Union
from unittest import TestCase

from serialzy.api import StandardDataFormats
from serialzy.registry import DefaultSerializerRegistry


class EmptyEnvTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_no_serializers_are_registered(self):
        class A:
            pass

        self.registry.reload_registry()

        serializer = self.registry.find_serializer_by_type(A)
        self.assertIsNotNone(serializer)
        self.assertFalse(serializer.available())
        self.assertIn("cloudpickle", serializer.requirements())

        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.proto.name)
        self.assertIsNotNone(serializer)
        self.assertFalse(serializer.available())
        self.assertIn("pure-protobuf", serializer.requirements())

        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.pickle.name)
        self.assertIsNotNone(serializer)
        self.assertFalse(serializer.available())
        self.assertIn("cloudpickle", serializer.requirements())

        serializer = self.registry.find_serializer_by_data_format('catboost_quantized_pool')
        self.assertIsNotNone(serializer)
        self.assertFalse(serializer.available())
        self.assertIn("catboost", serializer.requirements())

        serializer = self.registry.find_serializer_by_data_format('cbm')
        self.assertIsNotNone(serializer)
        self.assertFalse(serializer.available())
        self.assertIn("catboost", serializer.requirements())

        serializer = self.registry.find_serializer_by_data_format('serialzy_union')
        self.assertIsNotNone(serializer)
        self.assertTrue(serializer.available())

        serializer = self.registry.find_serializer_by_type(Union[str, int])
        self.assertIsNotNone(serializer)
        self.assertTrue(serializer.available())

        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.primitive_type.name)
        self.assertIsNotNone(serializer)
        self.assertTrue(serializer.available())

        serializer = self.registry.find_serializer_by_type(int)
        self.assertIsNotNone(serializer)
        self.assertTrue(serializer.available())
