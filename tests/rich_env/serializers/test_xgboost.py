# noinspection PyPackageRequirements
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

        dataset = datasets.load_wine()
        x = dataset.data
        y = dataset.target
        x_train, self.x_test, y_train, _ = train_test_split(x, y, test_size=0.30)
        self.dt = xgboost.DMatrix(self.x_test)

        self.model = xgboost.XGBClassifier()
        self.model.fit(x_train, y_train)

    def test_serialization(self):
        deserialized_model = self.base_test(self.model, XGBoostSerializer)
        self.assertTrue(np.allclose(self.model.predict_proba(self.x_test), deserialized_model.predict(self.dt)))

    def test_unpack(self):
        with self.base_unpack_test(self.model, XGBoostSerializer) as test_dir_name:
            deserialized_model = xgboost.Booster({'nthread': 4})
            deserialized_model.load_model(test_dir_name + "/model")

        self.assertTrue(np.allclose(self.model.predict_proba(self.x_test), deserialized_model.predict(self.dt)))

    def test_serialization_with_meta(self):
        deserialized_model = self.base_test_with_meta(self.model, XGBoostSerializer)
        self.assertTrue(np.allclose(self.model.predict_proba(self.x_test), deserialized_model.predict(self.dt)))

    def test_schema(self):
        self.base_schema('xgb', xgboost.XGBRanker)

    def test_resolve(self):
        self.base_resolve('xgb', xgboost.XGBClassifier)

    def test_invalid_types(self):
        self.base_invalid_types(self.model, xgboost.XGBRegressor)
