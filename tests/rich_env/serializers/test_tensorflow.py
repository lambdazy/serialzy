# noinspection PyPackageRequirements
import tempfile

import numpy as np
# noinspection PyPackageRequirements
import tensorflow as tf

from serialzy.serializers.tensorflow import TensorflowKerasSerializer, TensorflowPureSerializer
from tests.rich_env.serializers.test_base_model import ModelBaseSerializerTests


class MyModel(tf.keras.Model):
    def __init__(self):
        super(MyModel, self).__init__()
        self.dense1 = tf.keras.layers.Dense(4, activation=tf.nn.relu, input_shape=(32,))
        self.dense2 = tf.keras.layers.Dense(5, activation=tf.nn.softmax)

    def call(self, inputs, **kwargs):
        y = self.dense1(inputs)
        return self.dense2(y)


class TensorflowKerasSerializerTests(ModelBaseSerializerTests):
    def setUp(self):
        self.initialize("keras")

    def test_serialization_keras_sequential(self):
        model = tf.keras.Sequential([tf.keras.layers.Dense(5, input_shape=(3,)), tf.keras.layers.Softmax()])
        deserialized_model = self.base_test(model, TensorflowKerasSerializer)

        x = tf.random.uniform((10, 3))
        self.assertTrue(np.allclose(model.predict(x), deserialized_model.predict(x)))

    def test_serialization_keras_sequential_with_meta(self):
        model = tf.keras.Sequential([tf.keras.layers.Dense(5, input_shape=(3,)), tf.keras.layers.Softmax()])
        deserialized_model = self.base_test_with_meta(model, TensorflowKerasSerializer)

        x = tf.random.uniform((10, 3))
        self.assertTrue(np.allclose(model.predict(x), deserialized_model.predict(x)))

    def test_serialization_keras_model_with_meta(self):
        input_x = tf.keras.layers.Input(shape=(32,))
        layer = tf.keras.layers.Dense(32)(input_x)
        model = tf.keras.Model(inputs=input_x, outputs=layer)
        deserialized_model = self.base_test_with_meta(model, TensorflowKerasSerializer)

        x = tf.random.uniform((10, 32))
        self.assertTrue(np.allclose(model.predict(x), deserialized_model.predict(x)))

    def test_unpack_custom_keras_model(self):
        model = MyModel()
        model.compile(loss=tf.keras.losses.MeanSquaredError(),
                      metrics=[tf.keras.metrics.MeanAbsoluteError()])
        x = np.random.random((10, 32))
        y = np.random.random((10, 1))
        model.fit(x, y)

        with self.base_unpack_test(model, TensorflowKerasSerializer) as test_dir_name:
            deserialized_model = tf.keras.models.load_model(test_dir_name + "/model.savedmodel")

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

    def test_serialization_custom_keras_model_with_meta(self):
        model = MyModel()
        model.compile(loss=tf.keras.losses.MeanSquaredError(),
                      metrics=[tf.keras.metrics.MeanAbsoluteError()])
        x = np.random.random((10, 32))
        y = np.random.random((10, 1))
        model.fit(x, y)
        deserialized_model = self.base_test_with_meta(model, TensorflowKerasSerializer)

        x = tf.random.uniform((10, 32))
        self.assertTrue(np.allclose(model.predict(x), deserialized_model.predict(x)))

    def test_invalid_types(self):
        model = tf.keras.Sequential([tf.keras.layers.Dense(5, input_shape=(3,)), tf.keras.layers.Softmax()])
        self.base_invalid_types(model, tf.keras.Sequential)

    def test_schema(self):
        self.base_schema('tf_keras', tf.keras.Sequential)

    def test_resolve(self):
        self.base_resolve('tf_keras', tf.keras.Sequential)


class TensorflowPureSerializerTests(ModelBaseSerializerTests):
    def setUp(self):
        self.initialize("tensorflow")

    def test_serialization_tf_module(self):
        model = tf.Module()
        model.v = tf.Variable([1.])
        deserialized_model = self.base_test(model, TensorflowPureSerializer)

        self.assertTrue(np.allclose(model.v, deserialized_model.v))

    def test_serialization_tf_module_with_meta(self):
        model = tf.Module()
        model.v = tf.Variable([1.])
        deserialized_model = self.base_test_with_meta(model, TensorflowPureSerializer)

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

    def test_serialization_tf_checkpoint_with_meta(self):
        model = tf.train.Checkpoint(v=tf.Variable(3.))
        model.f = tf.function(
            lambda x: model.v * x,
            input_signature=[tf.TensorSpec(shape=None, dtype=tf.float32)])
        deserialized_model = self.base_test_with_meta(model, TensorflowPureSerializer)

        self.assertTrue(np.allclose(model.v, deserialized_model.v))
        self.assertEqual(model.f(x=tf.constant(2.)).numpy(),
                         deserialized_model.f(x=tf.constant(2.)).numpy())

    def test_invalid_types(self):
        model = tf.Module()
        model.v = tf.Variable([1.])
        self.base_invalid_types(model, tf.train.Checkpoint)

    def test_schema(self):
        self.base_schema('tf_pure', tf.train.Checkpoint)

    def test_resolve(self):
        self.base_resolve('tf_pure', tf.train.Checkpoint)

    def test_load_generic_model(self):

        class Adder(tf.Module):
            @tf.function(input_signature=[tf.TensorSpec(shape=[], dtype=tf.float32)])
            def __call__(self, x):
                return x + x

        model = Adder()
        self.assertEqual(2, model(1))

        with tempfile.TemporaryDirectory(suffix='serialzy_models_tests') as dest_dir:
            tf.saved_model.save(model, dest_dir)
            loaded_model = tf.saved_model.load(dest_dir)

        self.assertEqual(2, loaded_model(1))

        deserialized_model = self.base_test_with_meta(loaded_model, TensorflowPureSerializer)

        self.assertEqual(2, deserialized_model(1))
