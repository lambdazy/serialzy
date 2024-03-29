from typing import Union, List
from unittest import TestCase

from serialzy.api import StandardDataFormats
from serialzy.registry import DefaultSerializerRegistry


class EmptyEnvTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()
        self.registry.reload_registry()

    def test_no_serializers_are_registered_cloudpickle(self):
        class A:
            pass

        serializer = self.registry.find_serializer_by_type(A)
        assert serializer
        self.assertIsNotNone(serializer)
        self.assertFalse(serializer.available())
        self.assertIn("cloudpickle", serializer.requirements())

        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.pickle.name)
        assert serializer
        self.assertIsNotNone(serializer)
        self.assertFalse(serializer.available())
        self.assertIn("cloudpickle", serializer.requirements())

    def test_no_serializers_are_registered_proto(self):
        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.proto.name)
        assert serializer
        self.assertIsNotNone(serializer)
        self.assertFalse(serializer.available())
        self.assertIn("pure-protobuf", serializer.requirements())

    def test_no_serializers_are_registered_catboost(self):
        serializer = self.registry.find_serializer_by_data_format('catboost_quantized_pool')
        assert serializer
        self.assertIsNotNone(serializer)
        self.assertFalse(serializer.available())
        self.assertIn("catboost", serializer.requirements())

        serializer = self.registry.find_serializer_by_data_format('cbm')
        assert serializer
        self.assertIsNotNone(serializer)
        self.assertFalse(serializer.available())
        self.assertIn("catboost", serializer.requirements())

    def test_no_serializers_are_registered_union(self):
        serializer = self.registry.find_serializer_by_data_format('serialzy_union_stable')
        assert serializer
        self.assertIsNotNone(serializer)
        self.assertTrue(serializer.available())

        serializer = self.registry.find_serializer_by_type(Union[str, int])
        assert serializer
        self.assertIsNotNone(serializer)
        self.assertTrue(serializer.available())

    def test_no_serializers_are_registered_primitive(self):
        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.primitive_type.name)
        assert serializer
        self.assertIsNotNone(serializer)
        self.assertTrue(serializer.available())

        serializer = self.registry.find_serializer_by_type(int)
        assert serializer
        self.assertIsNotNone(serializer)
        self.assertTrue(serializer.available())

    def test_no_serializers_are_registered_list(self):
        serializer = self.registry.find_serializer_by_type(List[int])
        assert serializer
        self.assertIsNotNone(serializer)
        self.assertTrue(serializer.available())

        serializer = self.registry.find_serializer_by_data_format("serialzy_sequence_stable")
        assert serializer
        self.assertIsNotNone(serializer)
        self.assertTrue(serializer.available())

        class A:
            pass

        serializer = self.registry.find_serializer_by_type(List[A])
        assert serializer
        self.assertIsNotNone(serializer)
        self.assertFalse(serializer.available())
        self.assertIn("cloudpickle", serializer.requirements())
