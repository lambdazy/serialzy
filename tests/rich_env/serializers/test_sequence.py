import sys
from typing import List, Tuple, Type, Any
from unittest import TestCase

from serialzy.api import Serializer, Schema
from serialzy.registry import DefaultSerializerRegistry
from serialzy.serializers.sequence import SequenceSerializerStable, SequenceSerializerUnstable
from tests.rich_env.serializers.utils import serialize_and_deserialize


class SequenceSerializationTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_find_by_type(self):
        self._check_serializer_found_by_type(List[str])
        self._check_serializer_found_by_type(Tuple[str])

        if sys.version_info >= (3, 9):
            self._check_serializer_found_by_type(list[str])
            self._check_serializer_found_by_type(tuple[str])

        self._check_serializer_found_by_instance([1, 2, 3])
        self._check_serializer_found_by_instance((1, 2, 3))

        serializer = self.registry.find_serializer_by_type(type([1, 2, 3]))
        # in this case cloudpickle is used
        self.assertNotEqual(SequenceSerializerStable, type(serializer))

        serializer = self.registry.find_serializer_by_type(List)
        # in this case cloudpickle is used
        self.assertNotEqual(SequenceSerializerStable, type(serializer))

    def test_schema(self):
        typ = List[str]

        serializer = self.registry.find_serializer_by_type(typ)
        self.assertTrue(serializer.available())
        self.assertTrue(len(serializer.requirements()) == 0)

        schema = serializer.schema(typ)
        self.assertEqual("serialzy_sequence_stable", schema.data_format)
        self.assertTrue("serialzy" in schema.meta)
        self.assertEqual("serialzy_sequence_schema", schema.schema_format)

        resolved = serializer.resolve(schema)
        self.assertEqual(typ, resolved)

        with self.assertRaisesRegex(ValueError, "Invalid schema format*"):
            serializer.resolve(
                Schema(
                    'serialzy_sequence_stable',
                    'invalid schema',
                    schema.schema_content,
                    {'serialzy': '0.0.0'}
                )
            )

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema('serialzy_sequence_stable', 'serialzy_sequence_schema', schema.schema_content,
                       {'serialzy': '10000.0.0'}))
            self.assertRegex(cm.output[0], 'WARNING:serialzy.serializers.sequence:Installed version of serialzy*')

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema('serialzy_sequence_stable', 'serialzy_sequence_schema', schema.schema_content, {}))
            self.assertRegex(cm.output[0], 'WARNING:serialzy.serializers.sequence:No serialzy version in meta*')

    def test_stable_serialization(self):
        serializer = self.registry.find_serializer_by_data_format("serialzy_sequence_stable")
        self.assertEqual(SequenceSerializerStable, type(serializer))

        self._check_serialized_and_deserialized([1, 2, 3], serializer)
        self._check_serialized_and_deserialized((1, 2, 3), serializer)

        self._check_serialized_and_deserialized([], serializer)
        self._check_serialized_and_deserialized((), serializer)

    def test_unstable_serialization(self):
        class A:
            def __init__(self, x: int):
                self.x = x

            def __eq__(self, other):
                return other.x == self.x

        serializer = self.registry.find_serializer_by_data_format("serialzy_sequence_unstable")
        self.assertEqual(SequenceSerializerUnstable, type(serializer))

        self._check_serialized_and_deserialized([A(1), A(2), A(3)], serializer)
        self._check_serialized_and_deserialized((A(1), A(2), A(3)), serializer)

        with self.assertRaisesRegex(ValueError, "Invalid object type*"):
            self._check_serialized_and_deserialized([], serializer)

        with self.assertRaisesRegex(ValueError, "Invalid object type*"):
            self._check_serialized_and_deserialized((), serializer)

    def _check_serializer_found_by_type(self, typ: Type) -> None:
        serializer = self.registry.find_serializer_by_type(typ)
        self.assertEqual(SequenceSerializerStable, type(serializer))

    def _check_serializer_found_by_instance(self, obj: Any) -> None:
        serializer = self.registry.find_serializer_by_instance(obj)
        self.assertEqual(SequenceSerializerStable, type(serializer))

    def _check_serialized_and_deserialized(self, obj: Any, serializer: Serializer) -> None:
        deserialized_obj = serialize_and_deserialize(serializer, obj)
        self.assertEqual(obj, deserialized_obj)

    def test_stable_serialization_tuple_various_types(self):
        serializer = self.registry.find_serializer_by_type(Tuple[str, int])
        self.assertEqual(SequenceSerializerStable, type(serializer))
        self._check_serialized_and_deserialized(("str", 42), serializer)

    def test_stable_serialization_tuple_various_types_unstable(self):
        serializer = self.registry.find_serializer_by_type(Tuple[str, List])
        self.assertEqual(SequenceSerializerUnstable, type(serializer))
        self._check_serialized_and_deserialized(("str", [1, 2, 3]), serializer)

    def test_stable_serialization_tuple_of_untyped_lists(self):
        serializer = self.registry.find_serializer_by_type(Tuple[List, List])
        self.assertEqual(SequenceSerializerUnstable, type(serializer))
        self._check_serialized_and_deserialized(([1], [2]), serializer)

    def test_stable_serialization_tuple_of_typed_lists(self):
        serializer = self.registry.find_serializer_by_type(Tuple[List[int], List[int]])
        self.assertEqual(SequenceSerializerStable, type(serializer))
        self._check_serialized_and_deserialized(([1], [2]), serializer)

    def test_stable_serialization_tuple_of_variable_length_stable_small(self):
        serializer = self.registry.find_serializer_by_type(Tuple[int, ...])
        self.assertEqual(SequenceSerializerStable, type(serializer))
        self._check_serialized_and_deserialized((1, 2, 3), serializer)

    def test_stable_serialization_tuple_of_variable_length_stable_large(self):
        serializer = self.registry.find_serializer_by_type(Tuple[int, ...])
        self.assertEqual(SequenceSerializerStable, type(serializer))
        self._check_serialized_and_deserialized(tuple(i for i in range(1000)), serializer)

    def test_stable_serialization_tuple_of_variable_length_unstable(self):
        serializer = self.registry.find_serializer_by_type(Tuple[List, ...])
        self.assertEqual(SequenceSerializerUnstable, type(serializer))
        self._check_serialized_and_deserialized(([1], [2], [3]), serializer)

    def test_stable_serialization_tuple_of_variable_length_unstable_large(self):
        serializer = self.registry.find_serializer_by_type(Tuple[List, ...])
        self.assertEqual(SequenceSerializerUnstable, type(serializer))
        self._check_serialized_and_deserialized(tuple([i] for i in range(1000)), serializer)
