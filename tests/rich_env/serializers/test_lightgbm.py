# noinspection PyPackageRequirements
import lightgbm
import numpy as np
from sklearn import datasets
from sklearn.model_selection import train_test_split

from serialzy.serializers.lightgbm import LightGBMSerializer
from tests.rich_env.serializers.test_base_model import ModelBaseSerializerTests


class LightGBMModelSerializationTests(ModelBaseSerializerTests):
    def setUp(self):
        self.initialize("lightgbm")

    def test_serialization(self):
        dataset = datasets.load_wine()
        x = dataset.data
        y = dataset.target
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.30)

        model = lightgbm.LGBMClassifier()
        model.fit(x_train, y_train)

        deserialized_model = self.base_test(model, LightGBMSerializer)
        self.assertTrue(np.allclose(model.predict_proba(x_test), deserialized_model.predict(x_test)))

    def test_serialization_with_meta(self):
        dataset = datasets.load_wine()
        x = dataset.data
        y = dataset.target
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.30)

        model = lightgbm.LGBMClassifier()
        model.fit(x_train, y_train)

        deserialized_model = self.base_test_with_meta(model, LightGBMSerializer)
        self.assertTrue(np.allclose(model.predict_proba(x_test), deserialized_model.predict(x_test)))

    def test_schema(self):
        self.base_schema('lgbm', lightgbm.LGBMRanker)

    def test_resolve(self):
        self.base_resolve('lgbm', lightgbm.LGBMClassifier)

    def test_invalid_types(self):
        dataset = datasets.load_wine()
        x = dataset.data
        y = dataset.target
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.30)

        model = lightgbm.LGBMClassifier()
        model.fit(x_train, y_train)
        self.base_invalid_types(model, lightgbm.LGBMRegressor)
