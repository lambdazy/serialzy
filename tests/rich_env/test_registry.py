from typing import Any, BinaryIO, Callable, Dict, Type, Union, Optional
from unittest import TestCase

from serialzy.api import Serializer, Schema, VersionBoundary
from serialzy.registry import DefaultSerializerRegistry


def generate_serializer(
        supported_types: Union[Type, Callable[[Type], bool]] = lambda x: True,
        available: bool = True,
        stable: bool = True,
) -> Type[Serializer]:
    class MockType:
        pass

    class TestSerializer(Serializer):
        def requirements(self) -> Dict[str, VersionBoundary]:
            return {}

        def schema(self, typ: Type) -> Schema:
            return Schema('', '', '')

        def resolve(self, schema: Schema) -> Type:
            return MockType

        def data_format(self) -> str:
            return "test_format"

        def meta(self) -> Dict[str, str]:
            return {}

        def _serialize(self, obj: Any, dest: BinaryIO) -> None:
            pass

        def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
            pass

        def stable(self) -> bool:
            return stable

        def available(self) -> bool:
            return available

        def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
            return supported_types

    return TestSerializer


class A:
    pass


class SerializationRegistryTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_register_unregister_serializer_for_type(self):
        serializer = generate_serializer(available=True, supported_types=A)()
        self.registry.register_serializer(serializer)
        self.assertEqual(self.registry.find_serializer_by_type(A), serializer)

        self.registry.unregister_serializer(serializer)
        self.assertNotEqual(self.registry.find_serializer_by_type(A), serializer)

    def test_register_unavailable_serializer(self):
        serializer = generate_serializer(available=False, supported_types=A)()
        self.registry.register_serializer(serializer)
        by_type = self.registry.find_serializer_by_type(A)
        assert by_type
        self.assertEqual(by_type, serializer)
        self.assertFalse(by_type.available())

    def test_register_stable_serializer(self):
        serializer = generate_serializer(available=True, stable=True, supported_types=A)()
        self.registry.register_serializer(serializer)
        by_type = self.registry.find_serializer_by_type(A)
        assert by_type
        self.assertEqual(by_type.stable(), serializer.stable())

    def test_register_unstable_serializer(self):
        serializer = generate_serializer(available=True, stable=False, supported_types=A)()
        self.registry.register_serializer(serializer)
        by_type = self.registry.find_serializer_by_type(A)
        assert by_type
        self.assertEqual(by_type.stable(), serializer.stable())

    def test_serializer_for_type_prioritized(self):
        serializer_for_type = generate_serializer(available=True, supported_types=A)()
        self.registry.register_serializer(serializer_for_type)
        self.assertEqual(self.registry.find_serializer_by_type(A), serializer_for_type)

        serializer_for_all = generate_serializer(
            available=True, supported_types=lambda x: True
        )()
        self.registry.register_serializer(serializer_for_all)
        self.assertEqual(self.registry.find_serializer_by_type(A), serializer_for_type)

        self.registry.unregister_serializer(serializer_for_type)
        self.assertEqual(self.registry.find_serializer_by_type(A), serializer_for_all)

    def test_priorities(self):
        serializer_for_type_priority_1 = generate_serializer(available=True, supported_types=lambda x: True)()
        self.registry.register_serializer(serializer_for_type_priority_1, priority=1)
        self.assertEqual(self.registry.find_serializer_by_type(A), serializer_for_type_priority_1)

        serializer_for_type_priority_0 = generate_serializer(available=True, supported_types=lambda x: True)()
        self.registry.register_serializer(serializer_for_type_priority_0, priority=0)
        self.assertEqual(self.registry.find_serializer_by_type(A), serializer_for_type_priority_0)

        self.registry.unregister_serializer(serializer_for_type_priority_0)
        self.assertEqual(self.registry.find_serializer_by_type(A), serializer_for_type_priority_1)

    def test_filters(self):
        class Accepting:
            pass

        serializer = generate_serializer(
            available=True,
            supported_types=lambda x: "Accepting" in x.__name__,
        )()
        self.registry.register_serializer(serializer)
        self.assertEqual(self.registry.find_serializer_by_type(Accepting), serializer)
        self.assertNotEqual(self.registry.find_serializer_by_type(A), serializer)

    def test_register_the_same_serializer(self):
        serializer_1 = generate_serializer()()
        self.registry.register_serializer(serializer_1)
        with self.assertRaises(ValueError):
            self.registry.register_serializer(serializer_1)

    def test_register_serializer_for_the_same_type(self):
        serializer_1 = generate_serializer(supported_types=A)()
        serializer_2 = generate_serializer(supported_types=A)()

        self.registry.register_serializer(serializer_1, 2)
        self.assertEqual(serializer_1, self.registry.find_serializer_by_type(A))

        self.registry.register_serializer(serializer_2, 1)
        self.assertEqual(serializer_2, self.registry.find_serializer_by_type(A))
