# noinspection PyPackageRequirements
import lightgbm
# noinspection PyPackageRequirements
import numpy as np
# noinspection PyPackageRequirements
from sklearn import datasets
# noinspection PyPackageRequirements
from sklearn.model_selection import train_test_split

from serialzy.serializers.lightgbm import LightGBMSerializer
from tests.rich_env.serializers.test_base_model import ModelBaseSerializerTests


class LightGBMModelSerializationTests(ModelBaseSerializerTests):
    def setUp(self):
        self.initialize("lightgbm")

        dataset = datasets.load_wine()
        x = dataset.data
        y = dataset.target
        x_train, self.x_test, y_train, _ = train_test_split(x, y, test_size=0.30)

        self.model = lightgbm.LGBMClassifier()
        self.model.fit(x_train, y_train)

    def test_serialization(self):
        deserialized_model = self.base_test(self.model, LightGBMSerializer)
        self.assertTrue(np.allclose(self.model.predict_proba(self.x_test), deserialized_model.predict(self.x_test)))

    def test_unpack(self):
        with self.base_unpack_test(self.model, LightGBMSerializer) as test_dir_name:
            model_file = test_dir_name + "/model"
            deserialized_model = lightgbm.Booster(model_file=model_file)

        self.assertTrue(np.allclose(self.model.predict_proba(self.x_test), deserialized_model.predict(self.x_test)))

    def test_serialization_with_meta(self):
        deserialized_model = self.base_test_with_meta(self.model, LightGBMSerializer)
        self.assertTrue(np.allclose(self.model.predict_proba(self.x_test), deserialized_model.predict(self.x_test)))

    def test_schema(self):
        self.base_schema('lgbm', lightgbm.LGBMRanker)

    def test_resolve(self):
        self.base_resolve('lgbm', lightgbm.LGBMClassifier)

    def test_invalid_types(self):
        self.base_invalid_types(self.model, lightgbm.LGBMRegressor)
