import unittest

from kube_service_selectors.utils import (
    get_label_name,
    label_conflict_suffix,
    map_to_prometheus_labels,
    sanitize_label_name,
    to_snake_case,
)


class TestServiceSelectorsCollector(unittest.TestCase):
    def test_sanitize_label_name(self):
        res = "test_string"
        for val in [
            "test_string",
            "test\\string",
            "test\\string",
            "test!string",
            "test string",
        ]:
            self.assertEqual(sanitize_label_name(val), res)

    def test_to_snake_case(self):
        res = "test_string"
        for val in ["testString", "TestString", "Test_string"]:
            self.assertEqual(to_snake_case(val), res)

    def test_get_label_name(self):
        value = "TestString"
        result = "test_string"
        self.assertEqual(get_label_name(value), result)
        prefix = "some"
        self.assertEqual(get_label_name(value, prefix), f"{prefix}_{result}")

    def test_label_conflict_suffix(self):
        value = "test_string"
        for i in range(10):
            self.assertEqual(
                label_conflict_suffix(value, i), f"{value}_conflict{i}"
            )

    def test_map_to_prometheus_empty_labels(self):
        result = map_to_prometheus_labels({})
        self.assertEqual(result, ([], []))

    def test_map_to_prometheus_labels(self):
        labels = {"key_1": "value_1", "key_2": "value_2", "key_3": "value_3"}
        prometheus_labels = {
            "label_key_1": "value_1",
            "label_key_2": "value_2",
            "label_key_3": "value_3",
        }
        result = map_to_prometheus_labels(labels)
        self.assertEqual(
            result,
            (list(prometheus_labels.keys()), list(prometheus_labels.values())),
        )

    def test_map_to_prometheus_labels_conflicts(self):
        labels = {
            "key_1": "value_4",
            "key.1": "value_2",
            "key/1": "value_3",
            "Key_1": "value_1",
        }
        prometheus_labels = {
            "label_key_1_conflict1": "value_1",
            "label_key_1_conflict2": "value_2",
            "label_key_1_conflict3": "value_3",
            "label_key_1_conflict4": "value_4",
        }
        result = map_to_prometheus_labels(labels)
        self.assertEqual(
            result,
            (list(prometheus_labels.keys()), list(prometheus_labels.values())),
        )
