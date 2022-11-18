from typing import List

import setuptools


def read_version(path="version"):
    with open(path) as file:
        return file.read().rstrip()


def read_requirements() -> List[str]:
    requirements = []
    with open("requirements.txt", "r") as file:
        for line in file:
            requirements.append(line.rstrip())
    return requirements


setuptools.setup(
    name="serialzy",
    version=read_version(),
    author="ʎzy developers",
    install_requires=read_requirements(),
    packages=[
        "serialzy",
        "serialzy/serializers"
    ],
    python_requires=">=3.7",
)
