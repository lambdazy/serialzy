from typing import List

import setuptools


def read_version(path="serialzy/version/version"):
    with open(path) as file:
        return file.read().rstrip()


def read_requirements() -> List[str]:
    requirements = []
    with open("requirements.txt", "r") as file:
        for line in file:
            requirements.append(line.rstrip())
    return requirements


def read_readme() -> str:
    with open("README.md", "r") as file:
        return file.read()


setuptools.setup(
    name="serialzy",
    version=read_version(),
    license="LICENSE",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10"
    ],
    author="ʎzy developers",
    install_requires=read_requirements(),
    package_data={
        "serialzy": ["version/version"],
    },
    packages=[
        "serialzy",
        "serialzy/serializers"
    ],
    python_requires=">=3.7",
    long_description=read_readme(),
    long_description_content_type='text/markdown'
)
