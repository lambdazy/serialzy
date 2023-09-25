import xgboost
# noinspection PyPackageRequirements
import numpy as np
# noinspection PyPackageRequirements
from sklearn import datasets
# noinspection PyPackageRequirements
from sklearn.model_selection import train_test_split

from serialzy.serializers.xgboost import XGBoostSerializer
from tests.rich_env.serializers.test_base_model import ModelBaseSerializerTests


class XGBoostModelSerializationTests(ModelBaseSerializerTests):
    def setUp(self):
        self.initialize("xgboost")

    def test_serialization(self):
        dataset = datasets.load_wine()
        x = dataset.data
        y = dataset.target
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.30)
        dt = xgboost.DMatrix(x_test)

        model = xgboost.XGBClassifier()
        model.fit(x_train, y_train)

        deserialized_model = self.base_test(model, XGBoostSerializer)
        self.assertTrue(np.allclose(model.predict_proba(x_test), deserialized_model.predict(dt)))

    def test_unpack(self):
        dataset = datasets.load_wine()
        x = dataset.data
        y = dataset.target
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.30)
        dt = xgboost.DMatrix(x_test)

        model = xgboost.XGBClassifier()
        model.fit(x_train, y_train)

        with self.base_unpack_test(model, XGBoostSerializer) as test_dir_name:
            deserialized_model = xgboost.Booster({'nthread': 4})
            deserialized_model.load_model(test_dir_name + "/model")

        self.assertTrue(np.allclose(model.predict_proba(x_test), deserialized_model.predict(dt)))

    def test_serialization_with_meta(self):
        dataset = datasets.load_wine()
        x = dataset.data
        y = dataset.target
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.30)
        dt = xgboost.DMatrix(x_test)

        model = xgboost.XGBClassifier()
        model.fit(x_train, y_train)

        deserialized_model = self.base_test_with_meta(model, XGBoostSerializer)
        self.assertTrue(np.allclose(model.predict_proba(x_test), deserialized_model.predict(dt)))

    def test_schema(self):
        self.base_schema('xgb', xgboost.XGBRanker)

    def test_resolve(self):
        self.base_resolve('xgb', xgboost.XGBClassifier)

    def test_invalid_types(self):
        dataset = datasets.load_wine()
        x = dataset.data
        y = dataset.target
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.30)

        model = xgboost.XGBClassifier()
        model.fit(x_train, y_train)
        self.base_invalid_types(model, xgboost.XGBRegressor)
