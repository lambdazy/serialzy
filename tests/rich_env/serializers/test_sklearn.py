import pickle
import sklearn.ensemble as skle
import numpy as np
from sklearn import datasets
from sklearn.model_selection import train_test_split

from serialzy.serializers.sklearn import SciKitLearnSerializer
from tests.rich_env.serializers.test_base_model import ModelBaseSerializerTests


class SklearnModelSerializationTests(ModelBaseSerializerTests):
    def setUp(self):
        self.initialize("sklearn")

        dataset = datasets.load_wine()
        x = dataset.data
        y = dataset.target
        x_train, x_test, y_train, _ = train_test_split(x, y, test_size=0.30)
        self.dt = x_test

        self.models = [
            skle.GradientBoostingRegressor(init='zero'),
            skle.GradientBoostingRegressor(init='zero'),
            skle.IsolationForest(),
            skle.ExtraTreesClassifier(),
            skle.ExtraTreesRegressor(),
            skle.RandomForestRegressor()
        ]

        for model in self.models:
            model.fit(x_train, y_train)

    def test_serialization(self):
        for model in self.models:
            self._test_serialization(model)

    def _test_serialization(self, model):
        deserialized_model = self.base_test(model, SciKitLearnSerializer)
        self.assertTrue(np.allclose(model.predict(self.dt), deserialized_model.predict(self.dt)))

    def test_unpack(self):
        for model in self.models:
            self._test_unpack(model)

    def _test_unpack(self, model):
        with self.base_unpack_test(model, SciKitLearnSerializer) as test_dir_name:
            with open(test_dir_name + "/model.pickle", "rb") as f:
                deserialized_model = pickle.load(f)

        self.assertTrue(np.allclose(model.predict(self.dt), deserialized_model.predict(self.dt)))

    def test_serialization_with_meta(self):
        for model in self.models:
            self._test_serialization_with_meta(model)

    def _test_serialization_with_meta(self, model):
        deserialized_model = self.base_test_with_meta(model, SciKitLearnSerializer)
        self.assertTrue(np.allclose(model.predict(self.dt), deserialized_model.predict(self.dt)))

    def test_schema(self):
        for model in self.models:
            self._test_schema(model)

    def _test_schema(self, model):
        self.base_schema('skl', type(model))

    def test_resolve(self):
        for model in self.models:
            self._test_resolve(model)

    def _test_resolve(self, model):
        self.base_resolve('skl', type(model))

    def test_invalid_types(self):
        for model in self.models:
            self._test_invalid_types(model)

    def _test_invalid_types(self, model):
        self.base_invalid_types(model, type(model))
