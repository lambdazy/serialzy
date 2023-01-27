import json
import tempfile
from json import JSONDecodeError
from typing import Any
from unittest import TestCase

# noinspection PyPackageRequirements
import numpy as np
# noinspection PyPackageRequirements
import tensorflow as tf
from serialzy.api import Schema

from serialzy.registry import DefaultSerializerRegistry
from serialzy.serializers.tensorflow import TensorflowKerasSerializer, TensorflowPureSerializer
from tests.rich_env.serializers.utils import serialize_and_deserialize


class MyModel(tf.keras.Model):

    def __init__(self):
        super(MyModel, self).__init__()
        self.dense1 = tf.keras.layers.Dense(4, activation=tf.nn.relu, input_shape=(32,))
        self.dense2 = tf.keras.layers.Dense(5, activation=tf.nn.softmax)

    def call(self, inputs):
        y = self.dense1(inputs)
        return self.dense2(y)


class TensorflowBaseSerializerTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def base_test(self, model: Any, expected_serializer):
        serializer = self.registry.find_serializer_by_type(type(model))
        deserialized_model = serialize_and_deserialize(serializer, model)

        self.assertTrue(isinstance(serializer, expected_serializer))
        self.assertTrue(serializer.stable())
        self.assertIn("tensorflow", serializer.meta())
        self.assertIn("tensorflow", serializer.requirements())
        return deserialized_model

    def base_resolve(self, data_format: str, class_type):
        serializer = self.registry.find_serializer_by_data_format(data_format)

        typ = serializer.resolve(
            Schema(data_format, 'serialzy_python_type_reference', json.dumps({
                "module": class_type.__module__,
                "name": class_type.__name__
            }), {'tensorflow': '0.0.0'}))
        self.assertEqual(class_type, typ)

        with self.assertRaisesRegex(TypeError, 'Invalid data format*'):
            serializer.resolve(
                Schema('invalid format', 'serialzy_python_type_reference', 'content', {'tensorflow': '1.0.0'}))

        with self.assertRaisesRegex(ValueError, 'Invalid schema format*'):
            serializer.resolve(
                Schema(data_format, 'invalid format', json.dumps({
                    "module": class_type.__module__,
                    "name": class_type.__name__
                }), {'tensorflow': '0.0.0'}))

        with self.assertRaisesRegex(JSONDecodeError, 'Expecting value*'):
            serializer.resolve(
                Schema(data_format, 'serialzy_python_type_reference', 'invalid json',
                       {'tensorflow': '1.0.0'}))

        with self.assertRaisesRegex(ValueError, 'Invalid schema content*'):
            serializer.resolve(
                Schema(data_format, 'serialzy_python_type_reference', json.dumps({
                    "module": class_type.__module__
                }), {'tensorflow': '0.0.0'}))

        with self.assertRaisesRegex(ValueError, 'Invalid schema content*'):
            serializer.resolve(
                Schema(data_format, 'serialzy_python_type_reference', json.dumps({
                    "name": class_type.__name__
                }), {'tensorflow': '0.0.0'}))

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema(data_format, 'serialzy_python_type_reference', json.dumps({
                    "module": class_type.__module__,
                    "name": class_type.__name__
                }), {}))
            self.assertRegex(cm.output[0], 'WARNING:serialzy.serializers.tensorflow:No tensorflow version in meta')

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema(data_format, 'serialzy_python_type_reference', json.dumps({
                    "module": class_type.__module__,
                    "name": class_type.__name__
                }), {'tensorflow': '1000.0.0'}))
            self.assertRegex(cm.output[0],
                             'WARNING:serialzy.serializers.tensorflow:Installed version of tensorflow*')


class TensorflowKerasSerializerTests(TensorflowBaseSerializerTests):
    def test_serialization_keras_sequential(self):
        model = tf.keras.Sequential([tf.keras.layers.Dense(5, input_shape=(3,)), tf.keras.layers.Softmax()])
        deserialized_model = self.base_test(model, TensorflowKerasSerializer)

        x = tf.random.uniform((10, 3))
        self.assertTrue(np.allclose(model.predict(x), deserialized_model.predict(x)))

    def test_serialization_keras_model(self):
        input_x = tf.keras.layers.Input(shape=(32,))
        layer = tf.keras.layers.Dense(32)(input_x)
        model = tf.keras.Model(inputs=input_x, outputs=layer)
        deserialized_model = self.base_test(model, TensorflowKerasSerializer)

        x = tf.random.uniform((10, 32))
        self.assertTrue(np.allclose(model.predict(x), deserialized_model.predict(x)))

    def test_serialization_custom_keras_model(self):
        model = MyModel()
        model.compile(loss=tf.keras.losses.MeanSquaredError(),
                      metrics=[tf.keras.metrics.MeanAbsoluteError()])
        x = np.random.random((10, 32))
        y = np.random.random((10, 1))
        model.fit(x, y)
        deserialized_model = self.base_test(model, TensorflowKerasSerializer)

        x = tf.random.uniform((10, 32))
        self.assertTrue(np.allclose(model.predict(x), deserialized_model.predict(x)))

    def test_invalid_types(self):
        serializer = self.registry.find_serializer_by_type(tf.keras.Sequential)

        with self.assertRaisesRegex(TypeError, 'Invalid object type*'):
            with tempfile.TemporaryFile() as file:
                serializer.serialize(1, file)

        model = tf.keras.Sequential([tf.keras.layers.Dense(5, input_shape=(3,)), tf.keras.layers.Softmax()])
        with tempfile.TemporaryFile() as file:
            serializer.serialize(model, file)
            file.flush()
            file.seek(0)

            with self.assertRaisesRegex(TypeError, 'Cannot deserialize data with schema type*'):
                serializer.deserialize(file, int)

    def test_schema(self):
        serializer = self.registry.find_serializer_by_data_format('tf_keras')
        schema = serializer.schema(tf.keras.Sequential)

        self.assertEqual('tf_keras', schema.data_format)
        self.assertEqual('serialzy_python_type_reference', schema.schema_format)
        self.assertTrue(len(schema.schema_content) > 0)
        self.assertTrue('tensorflow' in schema.meta)

    def test_resolve(self):
        self.base_resolve('tf_keras', tf.keras.Sequential)


class TensorflowPureSerializerTests(TensorflowBaseSerializerTests):
    def test_serialization_tf_module(self):
        model = tf.Module()
        model.v = tf.Variable([1.])
        deserialized_model = self.base_test(model, TensorflowPureSerializer)

        self.assertTrue(np.allclose(model.v, deserialized_model.v))

    def test_serialization_tf_checkpoint(self):
        model = tf.train.Checkpoint(v=tf.Variable(3.))
        model.f = tf.function(
            lambda x: model.v * x,
            input_signature=[tf.TensorSpec(shape=None, dtype=tf.float32)])
        deserialized_model = self.base_test(model, TensorflowPureSerializer)

        self.assertTrue(np.allclose(model.v, deserialized_model.v))
        self.assertEqual(model.f(x=tf.constant(2.)).numpy(),
                         deserialized_model.f(x=tf.constant(2.)).numpy())

    def test_invalid_types(self):
        serializer = self.registry.find_serializer_by_type(tf.train.Checkpoint)

        with self.assertRaisesRegex(TypeError, 'Invalid object type*'):
            with tempfile.TemporaryFile() as file:
                serializer.serialize(1, file)

        model = tf.Module()
        model.v = tf.Variable([1.])
        with tempfile.TemporaryFile() as file:
            serializer.serialize(model, file)
            file.flush()
            file.seek(0)

            with self.assertRaisesRegex(TypeError, 'Cannot deserialize data with schema type*'):
                serializer.deserialize(file, int)

    def test_schema(self):
        serializer = self.registry.find_serializer_by_data_format('tf_pure')
        schema = serializer.schema(tf.train.Checkpoint)

        self.assertEqual('tf_pure', schema.data_format)
        self.assertEqual('serialzy_python_type_reference', schema.schema_format)
        self.assertTrue(len(schema.schema_content) > 0)
        self.assertTrue('tensorflow' in schema.meta)

    def test_resolve(self):
        self.base_resolve('tf_pure', tf.train.Checkpoint)
