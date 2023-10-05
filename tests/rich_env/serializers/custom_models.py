# noinspection PyPackageRequirements
import torch
# noinspection PyPackageRequirements
import tensorflow as tf


class MyKerasModel(tf.keras.Model):
    def __init__(self):
        super(MyKerasModel, self).__init__()
        self.dense1 = tf.keras.layers.Dense(4, activation=tf.nn.relu, input_shape=(32,))
        self.dense2 = tf.keras.layers.Dense(5, activation=tf.nn.softmax)

    def call(self, inputs, **kwargs):
        y = self.dense1(inputs)
        return self.dense2(y)


class MyTorchModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.sequential = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(100, 4),
            torch.nn.Dropout(0.5))

    def forward(self, x):
        return self.sequential(x)
