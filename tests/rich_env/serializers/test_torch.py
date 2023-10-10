# noinspection PyPackageRequirements
import torch
# noinspection PyPackageRequirements
import numpy as np

from serialzy.serializers.torch import TorchSerializer
from tests.rich_env.serializers.custom_models import MyTorchModel
from tests.rich_env.serializers.test_base_model import ModelBaseSerializerTests


class TorchSerializationTests(ModelBaseSerializerTests):
    def setUp(self):
        self.initialize("torch")

        self.x = torch.tensor(np.random.random(100).astype(np.float32).reshape(1, 1, 10, 10))
        self.model = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(100, 4),
            torch.nn.Dropout(0.5))
        self.model.eval()

        self.custom_model = MyTorchModel()
        self.custom_model.eval()

    def test_serialization_sequential(self):
        deserialized_model = self.base_test(self.model, TorchSerializer)
        self.assertTrue(np.allclose(self.model(self.x).tolist(), deserialized_model(self.x).tolist()))

    def test_serialization_sequential_with_meta(self):
        deserialized_model = self.base_test_with_meta(self.model, TorchSerializer)
        self.assertTrue(np.allclose(self.model(self.x).tolist(), deserialized_model(self.x).tolist()))

    def test_serialization_custom_model(self):
        deserialized_model = self.base_test(self.custom_model, TorchSerializer)
        self.assertTrue(np.allclose(self.custom_model(self.x).tolist(), deserialized_model(self.x).tolist()))

    def test_unpack_custom_model(self):
        with self.base_unpack_test(self.custom_model, TorchSerializer) as test_dir_name:
            deserialized_model = torch.jit.load(test_dir_name + "/model.pt")

        self.assertTrue(np.allclose(self.custom_model(self.x).tolist(), deserialized_model(self.x).tolist()))

    def test_serialization_custom_model_with_meta(self):
        deserialized_model = self.base_test_with_meta(self.custom_model, TorchSerializer)
        self.assertTrue(np.allclose(self.custom_model(self.x).tolist(), deserialized_model(self.x).tolist()))

    def test_schema(self):
        self.base_schema('pt', MyTorchModel)

    def test_resolve(self):
        self.base_resolve('pt', torch.nn.Sequential)

    def test_invalid_types(self):
        self.base_invalid_types(self.custom_model, torch.nn.Sequential)
