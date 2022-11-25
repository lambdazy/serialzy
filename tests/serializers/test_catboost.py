import json
import tempfile
from json import JSONDecodeError
from unittest import TestCase

# noinspection PyPackageRequirements
from catboost import Pool

from serialzy.api import Schema
from serialzy.serializers.catboost import CatboostPoolSerializer
from serialzy.registry import DefaultSerializerRegistry


class CatboostPoolSerializationTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_serialization(self):
        pool = Pool(
            data=[[1, 4, 5, 6], [4, 5, 6, 7], [30, 40, 50, 60]],
            label=[1, 1, -1],
            weight=[0.1, 0.2, 0.3],
        )
        serializer = self.registry.find_serializer_by_type(type(pool))
        with tempfile.TemporaryFile() as file:
            serializer.serialize(pool, file)
            file.flush()
            file.seek(0)
            deserialized_pool = serializer.deserialize(file, Pool)

        self.assertTrue(isinstance(serializer, CatboostPoolSerializer))
        self.assertEqual(pool.get_weight(), deserialized_pool.get_weight())
        self.assertTrue(serializer.stable())
        self.assertIn("catboost", serializer.meta())

    def test_schema(self):
        serializer = self.registry.find_serializer_by_data_format('catboost.core.Pool')
        schema = serializer.schema(Pool)

        self.assertEqual('catboost.core.Pool', schema.data_format)
        self.assertEqual('serialzy_python_type_reference', schema.schema_format)
        self.assertTrue(len(schema.schema_content) > 0)
        self.assertTrue('catboost' in schema.meta)

    def test_resolve(self):
        serializer = self.registry.find_serializer_by_data_format('catboost.core.Pool')

        typ = serializer.resolve(
            Schema('catboost.core.Pool', 'serialzy_python_type_reference', json.dumps({
                "module": Pool.__module__,
                "name": Pool.__name__
            }), {'catboost': '0.0.0'}))
        self.assertEqual(Pool, typ)

        with self.assertRaisesRegex(ValueError, 'Invalid data format*'):
            serializer.resolve(
                Schema('invalid format', 'serialzy_python_type_reference', 'content', {'catboost': '1.0.0'}))

        with self.assertRaisesRegex(ValueError, 'Invalid schema format*'):
            serializer.resolve(
                Schema('catboost.core.Pool', 'invalid format', json.dumps({
                    "module": Pool.__module__,
                    "name": Pool.__name__
                }), {'catboost': '0.0.0'}))

        with self.assertRaisesRegex(JSONDecodeError, 'Expecting value*'):
            serializer.resolve(
                Schema('catboost.core.Pool', 'serialzy_python_type_reference', 'invalid json', {'catboost': '1.0.0'}))

        with self.assertRaisesRegex(ValueError, 'Invalid schema content*'):
            serializer.resolve(
                Schema('catboost.core.Pool', 'serialzy_python_type_reference', json.dumps({
                    "module": Pool.__module__
                }), {'catboost': '0.0.0'}))

        with self.assertRaisesRegex(ValueError, 'Invalid schema content*'):
            serializer.resolve(
                Schema('catboost.core.Pool', 'serialzy_python_type_reference', json.dumps({
                    "name": Pool.__name__
                }), {'catboost': '0.0.0'}))

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema('catboost.core.Pool', 'serialzy_python_type_reference', json.dumps({
                    "module": Pool.__module__,
                    "name": Pool.__name__
                }), {}))
            self.assertRegex(cm.output[0], 'WARNING:serialzy.serializers.catboost:No catboost version in meta')

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema('catboost.core.Pool', 'serialzy_python_type_reference', json.dumps({
                    "module": Pool.__module__,
                    "name": Pool.__name__
                }), {'catboost': '1000.0.0'}))
            self.assertRegex(cm.output[0], 'WARNING:serialzy.serializers.catboost:Installed version of catboost*')
