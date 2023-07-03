from unittest import TestCase
import tempfile

from serialzy.registry import DefaultSerializerRegistry


class SerializationFailuresTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_empty(self):
        serializer = self.registry.find_serializer_by_type(int)
        with tempfile.TemporaryFile() as file:
            with self.assertRaisesRegex(ValueError, "Source is empty*"):
                serializer.deserialize(file)

    def test_no_header(self):
        serializer = self.registry.find_serializer_by_type(int)
        with tempfile.TemporaryFile() as file:
            file.write(b'12345')
            file.seek(0)
            with self.assertRaisesRegex(ValueError, "Missing header in source, expected b'serialzy', got b'12345'*"):
                serializer.deserialize(file)
