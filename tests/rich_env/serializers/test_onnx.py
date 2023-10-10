import tempfile
from typing import Any, Callable

# noinspection PyPackageRequirements
import numpy as np
# noinspection PyPackageRequirements
import torch

# noinspection PyPackageRequirements
import onnx
import onnxruntime  # type: ignore

from serialzy.serializers.onnx import ONNXSerializer
from tests.rich_env.serializers.custom_models import SuperResolutionNet
from tests.rich_env.serializers.test_base_model import ModelBaseSerializerTests
from tests.rich_env.serializers.utils import to_numpy


class ONNXModelSerializationTests(ModelBaseSerializerTests):
    def setUp(self) -> None:
        self.initialize("onnx")

        self.torch_model = SuperResolutionNet(upscale_factor=3)
        self.torch_model.eval()

        self.x_test = torch.randn(1, 1, 224, 224, requires_grad=True)

    def test_serialization(self):
        self._base_onnx_test(lambda model: self.base_test(model, ONNXSerializer))

    def test_serialization_with_meta(self):
        self._base_onnx_test(lambda model: self.base_test_with_meta(model, ONNXSerializer))

    def test_unpack(self):
        def unpack(model: onnx.ModelProto) -> onnx.ModelProto:
            with self.base_unpack_test(model, ONNXSerializer) as test_dir_name:
                return onnx.load(test_dir_name + "/model.onnx")

        self._base_onnx_test(unpack)

    def test_schema(self):
        self.base_schema('onnx', onnx.ModelProto)

    def test_resolve(self):
        self.base_resolve('onnx', onnx.ModelProto)

    def test_invalid_types(self):
        self.base_invalid_types(self._export_to_onnx(self.torch_model), onnx.ModelProto)

    def _base_onnx_test(self, serialization_routine: Callable[[onnx.ModelProto], onnx.ModelProto]) -> None:
        torch_out = self._infer_with_torch_model(self.torch_model)
        deserialized_model = serialization_routine(self._export_to_onnx(self.torch_model))
        ort_outs = self._infer_with_onnx_model(deserialized_model)
        # compare ONNX Runtime and PyTorch results
        self.assertTrue(np.allclose(to_numpy(torch_out), ort_outs[0], rtol=1e-03, atol=1e-05))

    def _infer_with_torch_model(self, model: torch.nn.Module) -> Any:
        return model(self.x_test)

    def _infer_with_onnx_model(self, model: onnx.ModelProto) -> Any:
        with tempfile.NamedTemporaryFile("wb") as f:
            f.write(model.SerializeToString())
            ort_session = onnxruntime.InferenceSession(f.name, providers=["CPUExecutionProvider"])

        ort_inputs = {ort_session.get_inputs()[0].name: to_numpy(self.x_test)}
        return ort_session.run(None, ort_inputs)

    def _export_to_onnx(self, model: torch.nn.Module) -> onnx.ModelProto:
        x = torch.randn(1, 1, 224, 224, requires_grad=True)

        with tempfile.NamedTemporaryFile("w+b") as f:
            torch.onnx.export(model,  # model being run
                              x,  # model input (or a tuple for multiple inputs)
                              f,  # where to save the model (can be a file or file-like object)
                              export_params=True,  # store the trained parameter weights inside the model file
                              opset_version=10,  # the ONNX version to export the model to
                              do_constant_folding=True,  # whether to execute constant folding for optimization
                              input_names=['input'],  # the model's input names
                              output_names=['output'],  # the model's output names
                              dynamic_axes={'input': {0: 'batch_size'},  # variable length axes
                                            'output': {0: 'batch_size'}})
            f.seek(0)
            onnx_model = onnx.load(f)
            onnx.checker.check_model(onnx_model)
            return onnx_model
