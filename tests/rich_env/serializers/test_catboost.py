import json
import tempfile
from json import JSONDecodeError
from unittest import TestCase

# noinspection PyPackageRequirements
import numpy
# noinspection PyPackageRequirements
from catboost import Pool, CatBoostRegressor, CatBoostRanker, CatBoostClassifier

from serialzy.api import Schema
from serialzy.errors import SerialzyError
from serialzy.registry import DefaultSerializerRegistry
from serialzy.serializers.catboost import CatboostPoolSerializer, CatboostModelSerializer
from tests.rich_env.serializers.utils import serialize_and_deserialize


class CatboostPoolSerializationTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_serialization(self):
        pool = Pool(
            data=[[1, 4, 5, 6], [4, 5, 6, 7], [30, 40, 50, 60]],
            label=[1, 1, -1],
            weight=[0.1, 0.2, 0.3],
        )
        pool.quantize()
        serializer = self.registry.find_serializer_by_type(type(pool))
        deserialized_pool = serialize_and_deserialize(serializer, pool)

        self.assertTrue(isinstance(serializer, CatboostPoolSerializer))
        self.assertEqual(pool.get_weight(), deserialized_pool.get_weight())
        self.assertTrue(serializer.stable())
        self.assertIn("catboost", serializer.meta())
        self.assertIn("catboost", serializer.requirements())

    def test_serialization_not_quantized(self):
        pool = Pool(
            data=[[1, 4, 5, 6], [4, 5, 6, 7], [30, 40, 50, 60]],
            label=[1, 1, -1],
            weight=[0.1, 0.2, 0.3],
        )
        serializer = self.registry.find_serializer_by_type(type(pool))
        with self.assertRaisesRegex(SerialzyError, 'nly quantized pools can be serialized*'):
            serialize_and_deserialize(serializer, pool)

    def test_invalid_types(self):
        serializer = self.registry.find_serializer_by_type(Pool)

        with self.assertRaisesRegex(ValueError, 'Invalid object type*'):
            with tempfile.TemporaryFile() as file:
                serializer.serialize(1, file)

        pool = Pool(
            data=[[1, 4, 5, 6], [4, 5, 6, 7], [30, 40, 50, 60]],
            label=[1, 1, -1],
            weight=[0.1, 0.2, 0.3],
        )
        pool.quantize()
        with tempfile.TemporaryFile() as file:
            serializer.serialize(pool, file)
            file.flush()
            file.seek(0)

            with self.assertRaisesRegex(ValueError, 'Cannot deserialize data with schema type*'):
                serializer.deserialize(file, int)

    def test_schema(self):
        serializer = self.registry.find_serializer_by_data_format('catboost_quantized_pool')
        schema = serializer.schema(Pool)

        self.assertEqual('catboost_quantized_pool', schema.data_format)
        self.assertEqual('serialzy_python_type_reference', schema.schema_format)
        self.assertTrue(len(schema.schema_content) > 0)
        self.assertTrue('catboost' in schema.meta)

    def test_resolve(self):
        serializer = self.registry.find_serializer_by_data_format('catboost_quantized_pool')

        typ = serializer.resolve(
            Schema('catboost_quantized_pool', 'serialzy_python_type_reference', json.dumps({
                "module": Pool.__module__,
                "name": Pool.__name__
            }), {'catboost': '0.0.0'}))
        self.assertEqual(Pool, typ)

        with self.assertRaisesRegex(ValueError, 'Invalid data format*'):
            serializer.resolve(
                Schema('invalid format', 'serialzy_python_type_reference', 'content', {'catboost': '1.0.0'}))

        with self.assertRaisesRegex(ValueError, 'Invalid schema format*'):
            serializer.resolve(
                Schema('catboost_quantized_pool', 'invalid format', json.dumps({
                    "module": Pool.__module__,
                    "name": Pool.__name__
                }), {'catboost': '0.0.0'}))

        with self.assertRaisesRegex(JSONDecodeError, 'Expecting value*'):
            serializer.resolve(
                Schema('catboost_quantized_pool', 'serialzy_python_type_reference', 'invalid json',
                       {'catboost': '1.0.0'}))

        with self.assertRaisesRegex(ValueError, 'Invalid schema content*'):
            serializer.resolve(
                Schema('catboost_quantized_pool', 'serialzy_python_type_reference', json.dumps({
                    "module": Pool.__module__
                }), {'catboost': '0.0.0'}))

        with self.assertRaisesRegex(ValueError, 'Invalid schema content*'):
            serializer.resolve(
                Schema('catboost_quantized_pool', 'serialzy_python_type_reference', json.dumps({
                    "name": Pool.__name__
                }), {'catboost': '0.0.0'}))

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema('catboost_quantized_pool', 'serialzy_python_type_reference', json.dumps({
                    "module": Pool.__module__,
                    "name": Pool.__name__
                }), {}))
            self.assertRegex(cm.output[0], 'WARNING:serialzy.serializers.catboost:No catboost version in meta')

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema('catboost_quantized_pool', 'serialzy_python_type_reference', json.dumps({
                    "module": Pool.__module__,
                    "name": Pool.__name__
                }), {'catboost': '1000.0.0'}))
            self.assertRegex(cm.output[0],
                             'WARNING:serialzy.serializers.catboost:Installed version of catboost*')


class CatboostModelSerializationTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_serialization(self):
        # example from https://catboost.ai/en/docs/concepts/python-usages-examples
        # noinspection DuplicatedCode
        train_data = [[1, 4, 5, 6],
                      [4, 5, 6, 7],
                      [30, 40, 50, 60]]
        train_labels = [10, 20, 30]
        model = CatBoostRegressor(iterations=2, learning_rate=1, depth=2, silent=True)
        model.fit(train_data, train_labels)

        serializer = self.registry.find_serializer_by_type(type(model))
        deserialized_model = serialize_and_deserialize(serializer, model)

        self.assertTrue(isinstance(serializer, CatboostModelSerializer))
        numpy.testing.assert_array_equal(model.get_leaf_weights(), deserialized_model.get_leaf_weights())
        self.assertTrue(serializer.stable())
        self.assertIn("catboost", serializer.meta())

    def test_schema(self):
        serializer = self.registry.find_serializer_by_data_format('cbm')
        schema = serializer.schema(CatBoostRanker)

        self.assertEqual('cbm', schema.data_format)
        self.assertEqual('serialzy_python_type_reference', schema.schema_format)
        self.assertTrue(len(schema.schema_content) > 0)
        self.assertTrue('catboost' in schema.meta)

    def test_resolve(self):
        serializer = self.registry.find_serializer_by_data_format('cbm')

        typ = serializer.resolve(
            Schema('cbm', 'serialzy_python_type_reference', json.dumps({
                "module": CatBoostClassifier.__module__,
                "name": CatBoostClassifier.__name__
            }), {'catboost': '0.0.0'}))
        self.assertEqual(CatBoostClassifier, typ)

    def test_invalid_types(self):
        serializer = self.registry.find_serializer_by_type(CatBoostClassifier)

        with self.assertRaisesRegex(ValueError, 'Invalid object type*'):
            with tempfile.TemporaryFile() as file:
                serializer.serialize(1, file)

        # example from https://catboost.ai/en/docs/concepts/python-usages-examples
        # noinspection DuplicatedCode
        train_data = [[1, 4, 5, 6],
                      [4, 5, 6, 7],
                      [30, 40, 50, 60]]
        train_labels = [10, 20, 30]
        model = CatBoostRegressor(iterations=2, learning_rate=1, depth=2, silent=True)
        model.fit(train_data, train_labels)

        with tempfile.TemporaryFile() as file:
            serializer.serialize(model, file)
            file.flush()
            file.seek(0)

            with self.assertRaisesRegex(ValueError, 'Cannot deserialize data with schema type*'):
                serializer.deserialize(file, int)
