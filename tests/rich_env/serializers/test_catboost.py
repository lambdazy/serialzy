# noinspection PyPackageRequirements
import numpy
# noinspection PyPackageRequirements
from catboost import Pool, CatBoostRegressor, CatBoostRanker, CatBoostClassifier

from serialzy.errors import SerialzyError
from serialzy.serializers.catboost import CatboostPoolSerializer, CatboostModelSerializer
from tests.rich_env.serializers.test_base_model import ModelBaseSerializerTests
from tests.rich_env.serializers.utils import serialize_and_deserialize


class CatboostPoolSerializationTests(ModelBaseSerializerTests):
    def setUp(self):
        self.initialize("catboost")

    def test_serialization(self):
        pool = Pool(
            data=[[1, 4, 5, 6], [4, 5, 6, 7], [30, 40, 50, 60]],
            label=[1, 1, -1],
            weight=[0.1, 0.2, 0.3],
        )
        pool.quantize()
        deserialized_pool = self.base_test(pool, CatboostPoolSerializer)
        self.assertEqual(pool.get_weight(), deserialized_pool.get_weight())

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
        pool = Pool(
            data=[[1, 4, 5, 6], [4, 5, 6, 7], [30, 40, 50, 60]],
            label=[1, 1, -1],
            weight=[0.1, 0.2, 0.3],
        )
        pool.quantize()
        self.base_invalid_types(pool, Pool)

    def test_schema(self):
        self.base_schema('catboost_quantized_pool', Pool)

    def test_resolve(self):
        self.base_resolve('catboost_quantized_pool', Pool)


class CatboostModelSerializationTests(ModelBaseSerializerTests):
    def setUp(self):
        self.initialize("catboost")

    def test_serialization(self):
        # example from https://catboost.ai/en/docs/concepts/python-usages-examples
        # noinspection DuplicatedCode
        train_data = [[1, 4, 5, 6],
                      [4, 5, 6, 7],
                      [30, 40, 50, 60]]
        train_labels = [10, 20, 30]
        model = CatBoostRegressor(iterations=2, learning_rate=1, depth=2, silent=True)
        model.fit(train_data, train_labels)

        deserialized_model = self.base_test(model, CatboostModelSerializer)
        numpy.testing.assert_array_equal(model.get_leaf_weights(), deserialized_model.get_leaf_weights())

    def test_schema(self):
        self.base_schema('cbm', CatBoostRanker)

    def test_resolve(self):
        self.base_resolve('cbm', CatBoostClassifier)

    def test_invalid_types(self):
        train_data = [[1, 4, 5, 6],
                      [4, 5, 6, 7],
                      [30, 40, 50, 60]]
        train_labels = [10, 20, 30]
        model = CatBoostRegressor(iterations=2, learning_rate=1, depth=2, silent=True)
        model.fit(train_data, train_labels)
        self.base_invalid_types(model, CatBoostClassifier)
