import tempfile

# noinspection PyPackageRequirements
import numpy as np
# noinspection PyPackageRequirements
import tensorflow as tf

from serialzy.serializers.tensorflow import TensorflowKerasSerializer, TensorflowPureSerializer
from tests.rich_env.serializers.custom_models import MyKerasModel
from tests.rich_env.serializers.test_base_model import ModelBaseSerializerTests


class TensorflowKerasSerializerTests(ModelBaseSerializerTests):
    def setUp(self):
        self.initialize("keras")
        self.sequential = tf.keras.Sequential([tf.keras.layers.Dense(5, input_shape=(3,)), tf.keras.layers.Softmax()])

        input_x = tf.keras.layers.Input(shape=(32,))
        layer = tf.keras.layers.Dense(32)(input_x)
        self.model = tf.keras.Model(inputs=input_x, outputs=layer)

        self.custom_model = MyKerasModel()
        self.custom_model.compile(loss=tf.keras.losses.MeanSquaredError(),
                                  metrics=[tf.keras.metrics.MeanAbsoluteError()])
        x = np.random.random((10, 32))
        y = np.random.random((10, 1))
        self.custom_model.fit(x, y)

    def test_serialization_keras_sequential(self):
        deserialized_model = self.base_test(self.sequential, TensorflowKerasSerializer)
        x = tf.random.uniform((10, 3))
        self.assertTrue(np.allclose(self.sequential.predict(x), deserialized_model.predict(x)))

    def test_serialization_keras_sequential_with_meta(self):
        deserialized_model = self.base_test_with_meta(self.sequential, TensorflowKerasSerializer)
        x = tf.random.uniform((10, 3))
        self.assertTrue(np.allclose(self.sequential.predict(x), deserialized_model.predict(x)))

    def test_serialization_keras_model(self):
        deserialized_model = self.base_test(self.model, TensorflowKerasSerializer)
        x = tf.random.uniform((10, 32))
        self.assertTrue(np.allclose(self.model.predict(x), deserialized_model.predict(x)))

    def test_serialization_keras_model_with_meta(self):
        deserialized_model = self.base_test_with_meta(self.model, TensorflowKerasSerializer)
        x = tf.random.uniform((10, 32))
        self.assertTrue(np.allclose(self.model.predict(x), deserialized_model.predict(x)))

    def test_unpack_custom_keras_model(self):
        with self.base_unpack_test(self.custom_model, TensorflowKerasSerializer) as test_dir_name:
            deserialized_model = tf.keras.models.load_model(test_dir_name + "/model.savedmodel")

        x = tf.random.uniform((10, 32))
        self.assertTrue(np.allclose(self.custom_model.predict(x), deserialized_model.predict(x)))

    def test_serialization_custom_keras_model(self):
        deserialized_model = self.base_test(self.custom_model, TensorflowKerasSerializer)
        x = tf.random.uniform((10, 32))
        self.assertTrue(np.allclose(self.custom_model.predict(x), deserialized_model.predict(x)))

    def test_serialization_custom_keras_model_with_meta(self):
        deserialized_model = self.base_test_with_meta(self.custom_model, TensorflowKerasSerializer)
        x = tf.random.uniform((10, 32))
        self.assertTrue(np.allclose(self.custom_model.predict(x), deserialized_model.predict(x)))

    def test_invalid_types(self):
        self.base_invalid_types(self.sequential, tf.keras.Sequential)

    def test_schema(self):
        self.base_schema('tf_keras', tf.keras.Sequential)

    def test_resolve(self):
        self.base_resolve('tf_keras', tf.keras.Sequential)


class TensorflowPureSerializerTests(ModelBaseSerializerTests):
    def setUp(self):
        self.initialize("tensorflow")

        self.tf_module = tf.Module()
        self.tf_module.v = tf.Variable([1.])

        self.checkpoint = tf.train.Checkpoint(v=tf.Variable(3.))
        self.checkpoint.f = tf.function(
            lambda x: self.checkpoint.v * x,
            input_signature=[tf.TensorSpec(shape=None, dtype=tf.float32)])

    def test_serialization_tf_module(self):
        deserialized_model = self.base_test(self.tf_module, TensorflowPureSerializer)
        self.assertTrue(np.allclose(self.tf_module.v, deserialized_model.v))

    def test_serialization_tf_module_with_meta(self):
        deserialized_model = self.base_test_with_meta(self.tf_module, TensorflowPureSerializer)
        self.assertTrue(np.allclose(self.tf_module.v, deserialized_model.v))

    def test_serialization_tf_checkpoint(self):
        deserialized_model = self.base_test(self.checkpoint, TensorflowPureSerializer)

        self.assertTrue(np.allclose(self.checkpoint.v, deserialized_model.v))
        self.assertEqual(self.checkpoint.f(x=tf.constant(2.)).numpy(),
                         deserialized_model.f(x=tf.constant(2.)).numpy())

    def test_serialization_tf_checkpoint_with_meta(self):
        deserialized_model = self.base_test_with_meta(self.checkpoint, TensorflowPureSerializer)

        self.assertTrue(np.allclose(self.checkpoint.v, deserialized_model.v))
        self.assertEqual(self.checkpoint.f(x=tf.constant(2.)).numpy(),
                         deserialized_model.f(x=tf.constant(2.)).numpy())

    def test_invalid_types(self):
        self.base_invalid_types(self.tf_module, tf.train.Checkpoint)

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
