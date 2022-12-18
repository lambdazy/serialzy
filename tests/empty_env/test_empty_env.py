from unittest import TestCase

from serialzy.api import StandardDataFormats
from serialzy.registry import DefaultSerializerRegistry


class EmptyEnvTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_no_serializers_are_registered(self):
        class A:
            pass

        serializer = self.registry.find_serializer_by_type(A)
        self.assertIsNone(serializer)

        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.proto.name)
        self.assertIsNone(serializer)

        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.pickle.name)
        self.assertIsNone(serializer)

        serializer = self.registry.find_serializer_by_data_format('catboost_quantized_pool')
        self.assertIsNone(serializer)

        serializer = self.registry.find_serializer_by_data_format('cbm')
        self.assertIsNone(serializer)
