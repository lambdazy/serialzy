from typing import Dict
from unittest import TestCase

from serialzy.types import get_type, EmptyContent


class A:
    pass


class SerializationRegistryTests(TestCase):
    def test_dict_inference(self):
        self.assertEqual(Dict[int, str], get_type({1: "1", 2: "2"}))
        self.assertEqual(Dict[int, A], get_type({1: A(), 2: A()}))
        self.assertEqual(Dict[EmptyContent, EmptyContent], get_type({}))
