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


class SklearnTreeModelSerializationTests(ModelBaseSerializerTests):
    def setUp(self):
        self.initialize("sklearn")

        dataset = datasets.load_wine()
        x = dataset.data
        y = dataset.target
        x_train, self.x_test, y_train, _ = train_test_split(x, y, test_size=0.30)
        self.dt = self.x_test

        self.model = skle.GradientBoostingClassifier(init='zero')
        self.model.fit(x_train, y_train)

    def test_serialization(self):
        deserialized_model = self.base_test(self.model, SciKitLearnSerializer)
        self.assertTrue(np.allclose(self.model.predict_proba(self.x_test), deserialized_model.predict_proba(self.dt)))

    def test_unpack(self):
        with self.base_unpack_test(self.model, SciKitLearnSerializer) as test_dir_name:
            with open(test_dir_name + "/model.pickle", "rb") as f:
                deserialized_model = pickle.load(f)

        self.assertTrue(np.allclose(self.model.predict_proba(self.x_test), deserialized_model.predict_proba(self.dt)))

    def test_serialization_with_meta(self):
        deserialized_model = self.base_test_with_meta(self.model, SciKitLearnSerializer)
        self.assertTrue(np.allclose(self.model.predict_proba(self.x_test), deserialized_model.predict_proba(self.dt)))

    def test_schema(self):
        self.base_schema('skl', skle.GradientBoostingClassifier)

    def test_resolve(self):
        self.base_resolve('skl', skle.GradientBoostingClassifier)

    def test_invalid_types(self):
        self.base_invalid_types(self.model, skle.GradientBoostingRegressor)
