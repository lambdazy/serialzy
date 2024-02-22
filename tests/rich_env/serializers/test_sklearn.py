# noinspection PyPackageRequirements
import pickle
import sklearn.ensemble as skle
# noinspection PyPackageRequirements
import numpy as np
# noinspection PyPackageRequirements
from sklearn import datasets
# noinspection PyPackageRequirements
from sklearn.model_selection import train_test_split

from serialzy.serializers.sklearn import SciKitLearnSerializer
from tests.rich_env.serializers.test_base_model import ModelBaseSerializerTests


class BaseSklearnModelSerializationTests(ModelBaseSerializerTests):
    def setUp(self):
        self.initialize("sklearn")

        dataset = datasets.load_wine()
        x = dataset.data
        y = dataset.target
        x_train, self.x_test, y_train, _ = train_test_split(x, y, test_size=0.30)
        self.dt = self.x_test

        self.model = self._get_model()
        self.model.fit(x_train, y_train)

    def _get_model(self):
        return None

    def base_test_serialization(self):
        deserialized_model = self.base_test(self.model, SciKitLearnSerializer)
        self.assertTrue(np.allclose(self.model.predict(self.x_test), deserialized_model.predict(self.dt)))

    def base_test_unpack(self):
        with self.base_unpack_test(self.model, SciKitLearnSerializer) as test_dir_name:
            with open(test_dir_name + "/model.pickle", "rb") as f:
                deserialized_model = pickle.load(f)

        self.assertTrue(np.allclose(self.model.predict(self.x_test), deserialized_model.predict(self.dt)))

    def base_test_serialization_with_meta(self):
        deserialized_model = self.base_test_with_meta(self.model, SciKitLearnSerializer)
        self.assertTrue(np.allclose(self.model.predict(self.x_test), deserialized_model.predict(self.dt)))

    def base_test_schema(self):
        self.base_schema('skl', type(self.model))

    def base_test_resolve(self):
        self.base_resolve('skl', type(self.model))

    def base_test_invalid_types(self):
        self.base_invalid_types(self.model, type(self.model))


class GradientBoostingClassifierSklearnModelSerializationTests(BaseSklearnModelSerializationTests):
    def _get_model(self):
        return skle.GradientBoostingClassifier(init='zero')

    def test_serialization(self):
        return super().base_test_serialization()

    def test_unpack(self):
        return super().base_test_unpack()

    def test_serialization_with_meta(self):
        return super().base_test_serialization_with_meta()

    def test_schema(self):
        return super().base_test_schema()

    def test_resolve(self):
        return super().base_test_resolve()

    def test_invalid_types(self):
        return super().base_test_invalid_types()


class GradientBoostingRegressorSklearnModelSerializationTests(BaseSklearnModelSerializationTests):
    def _get_model(self):
        return skle.GradientBoostingRegressor(init='zero')

    def test_serialization(self):
        return super().base_test_serialization()

    def test_unpack(self):
        return super().base_test_unpack()

    def test_serialization_with_meta(self):
        return super().base_test_serialization_with_meta()

    def test_schema(self):
        return super().base_test_schema()

    def test_resolve(self):
        return super().base_test_resolve()

    def test_invalid_types(self):
        return super().base_test_invalid_types()


class RandomForestRegressorSklearnModelSerializationTests(BaseSklearnModelSerializationTests):
    def _get_model(self):
        return skle.RandomForestRegressor()

    def test_serialization(self):
        return super().base_test_serialization()

    def test_unpack(self):
        return super().base_test_unpack()

    def test_serialization_with_meta(self):
        return super().base_test_serialization_with_meta()

    def test_schema(self):
        return super().base_test_schema()

    def test_resolve(self):
        return super().base_test_resolve()

    def test_invalid_types(self):
        return super().base_test_invalid_types()


class ExtraTreesClassifierSklearnModelSerializationTests(BaseSklearnModelSerializationTests):
    def _get_model(self):
        return skle.ExtraTreesClassifier()

    def test_serialization(self):
        return super().base_test_serialization()

    def test_unpack(self):
        return super().base_test_unpack()

    def test_serialization_with_meta(self):
        return super().base_test_serialization_with_meta()

    def test_schema(self):
        return super().base_test_schema()

    def test_resolve(self):
        return super().base_test_resolve()

    def test_invalid_types(self):
        return super().base_test_invalid_types()


class ExtraTreesRegressorSklearnModelSerializationTests(BaseSklearnModelSerializationTests):
    def _get_model(self):
        return skle.ExtraTreesRegressor()

    def test_serialization(self):
        return super().base_test_serialization()

    def test_unpack(self):
        return super().base_test_unpack()

    def test_serialization_with_meta(self):
        return super().base_test_serialization_with_meta()

    def test_schema(self):
        return super().base_test_schema()

    def test_resolve(self):
        return super().base_test_resolve()

    def test_invalid_types(self):
        return super().base_test_invalid_types()
