import sys
from typing import Tuple, Iterable

from serialzy.api import SerializerRegistry, Serializer
from serialzy.registry import DefaultSerializerRegistry
from serialzy.serializers.base_model import ModelBaseSerializer

from urllib.request import urlopen


def _download_and_unpack_model(registry: SerializerRegistry, url: str, dest_dir: str) -> None:
    with urlopen(url) as data:
        data_format = Serializer.deserialize_data_format(data)
        serializer = registry.find_serializer_by_data_format(data_format)

        if not isinstance(serializer, ModelBaseSerializer):
            raise ValueError(f"Data by source_url '{url}' is not a model")

        assert isinstance(serializer, ModelBaseSerializer)

        serializer.unpack_model(data, dest_dir)


def download_and_unpack_models(urls_and_dirs: Iterable[Tuple[str, str]]) -> None:
    registry = DefaultSerializerRegistry()
    for (source_url, dest_dir) in urls_and_dirs:
        _download_and_unpack_model(registry, source_url, dest_dir)


def main():
    argv = sys.argv[1:]

    if len(argv) < 2:
        raise ValueError("Missing required args: model urls list and destination file paths list")

    source_urls = argv[0].split(',')
    dest_dirs = argv[1].split(',')

    if len(source_urls) != len(dest_dirs):
        raise ValueError("Missing some model url or destination file path")

    download_and_unpack_models(zip(source_urls, dest_dirs))


if __name__ == "__main__":
    main()
