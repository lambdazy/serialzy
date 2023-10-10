# noinspection PyPackageRequirements
import torch
import torch.nn.init as init
# noinspection PyPackageRequirements
import tensorflow as tf


class MyKerasModel(tf.keras.Model):
    def __init__(self):
        super().__init__()
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


class SuperResolutionNet(torch.nn.Module):
    def __init__(self, upscale_factor, inplace=False):
        super(SuperResolutionNet, self).__init__()

        self.relu = torch.nn.ReLU(inplace=inplace)
        self.conv1 = torch.nn.Conv2d(1, 64, (5, 5), (1, 1), (2, 2))
        self.conv2 = torch.nn.Conv2d(64, 64, (3, 3), (1, 1), (1, 1))
        self.conv3 = torch.nn.Conv2d(64, 32, (3, 3), (1, 1), (1, 1))
        self.conv4 = torch.nn.Conv2d(32, upscale_factor ** 2, (3, 3), (1, 1), (1, 1))
        self.pixel_shuffle = torch.nn.PixelShuffle(upscale_factor)

        self._initialize_weights()

    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.relu(self.conv3(x))
        x = self.pixel_shuffle(self.conv4(x))
        return x

    def _initialize_weights(self):
        init.orthogonal_(self.conv1.weight, init.calculate_gain('relu'))
        init.orthogonal_(self.conv2.weight, init.calculate_gain('relu'))
        init.orthogonal_(self.conv3.weight, init.calculate_gain('relu'))
        init.orthogonal_(self.conv4.weight)
