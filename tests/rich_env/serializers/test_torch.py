import torch
# noinspection PyPackageRequirements
import numpy as np

from serialzy.serializers.torch import TorchSerializer
from tests.rich_env.serializers.test_base_model import ModelBaseSerializerTests


class MyModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.sequential = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(100, 4),
            torch.nn.Dropout(0.5))

    def forward(self, x):
        return self.sequential(x)


class TorchSerializationTests(ModelBaseSerializerTests):
    def setUp(self):
        self.initialize("torch")

    def test_serialization_sequential(self):
        x = torch.tensor(np.random.random(100).astype(np.float32).reshape(1, 1, 10, 10))
        model = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(100, 4),
            torch.nn.Dropout(0.5))
        model.eval()
        deserialized_model = self.base_test(model, TorchSerializer)
        self.assertTrue(np.allclose(model(x).tolist(), deserialized_model(x).tolist()))

    def test_serialization_custom_model(self):
        x = torch.tensor(np.random.random(100).astype(np.float32).reshape(1, 1, 10, 10))
        model = MyModel()
        model.eval()
        deserialized_model = self.base_test(model, TorchSerializer)
        self.assertTrue(np.allclose(model(x).tolist(), deserialized_model(x).tolist()))

    def test_schema(self):
        self.base_schema('pt', MyModel)

    def test_resolve(self):
        self.base_resolve('pt', torch.nn.Sequential)

    def test_invalid_types(self):
        model = MyModel()
        model.eval()
        self.base_invalid_types(model, torch.nn.Sequential)
