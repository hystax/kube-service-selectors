import unittest

from dataclasses import dataclass
from prometheus_client.metrics_core import GaugeMetricFamily
from unittest.mock import MagicMock

from kube_service_selectors.main import (
    ServiceSelectorsCollector,
    DEFAULT_LABELS,
    DEFAULT_LIMIT,
)
from kube_service_selectors.utils import LABEL_PREFIX


@dataclass
class V1ServiceSpecMock:
    selector: dict[str, str]


@dataclass
class V1ObjectMetaMock:
    name: str
    namespace: str
    uid: str


@dataclass
class V1ServiceMock:
    metadata: V1ObjectMetaMock
    spec: V1ServiceSpecMock


@dataclass
class V1ListMetaMock:
    _continue: str = None


@dataclass
class ServiceListResponseMock:
    items: list[V1ServiceMock]
    metadata: V1ListMetaMock


class TestServiceSelectorsCollector(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k8s_client_mock = MagicMock()
        self.namespaces = ["default"]
        self.collector = ServiceSelectorsCollector(self.k8s_client_mock)
        self.namespaced_collector = ServiceSelectorsCollector(
            self.k8s_client_mock, namespaces=self.namespaces
        )

    def check_result(
        self,
        result: GaugeMetricFamily,
        mocked_response: ServiceListResponseMock,
    ):
        self.assertTrue(result is not None)
        services_count = len(mocked_response.items)
        self.assertEqual(len(result.samples), services_count)
        for sample in result.samples:
            required_labels = {}
            optional_labels = {}
            for k, v in sample.labels.items():
                if k in DEFAULT_LABELS:
                    required_labels[k] = v
                else:
                    optional_labels[k] = v
            self.assertEqual(len(required_labels), len(DEFAULT_LABELS))
            self.assertTrue(
                all(
                    map(
                        lambda x: x.startswith(LABEL_PREFIX),
                        optional_labels.keys(),
                    )
                )
            )

    def test_all_namespaces_no_services(self):
        k8s_response = ServiceListResponseMock([], V1ListMetaMock())
        self.k8s_client_mock.list_service_for_all_namespaces.return_value = (
            k8s_response
        )
        res = next(self.collector.collect(), None)
        self.check_result(res, k8s_response)

    def test_namespaced_no_services(self):
        k8s_response = ServiceListResponseMock([], V1ListMetaMock())
        self.k8s_client_mock.list_namespaced_service.return_value = (
            k8s_response
        )
        res = next(self.namespaced_collector.collect(), None)
        self.check_result(res, k8s_response)

    def test_all_namespaces(self):
        k8s_response = ServiceListResponseMock(
            [
                V1ServiceMock(
                    V1ObjectMetaMock("name", "namespace", "uid"),
                    V1ServiceSpecMock({"key": "value"}),
                )
            ],
            V1ListMetaMock(),
        )
        self.k8s_client_mock.list_service_for_all_namespaces.return_value = (
            k8s_response
        )
        res = next(self.collector.collect(), None)
        self.check_result(res, k8s_response)

    def test_namespaced(self):
        k8s_response = ServiceListResponseMock(
            [
                V1ServiceMock(
                    V1ObjectMetaMock("name", "namespace", "uid"),
                    V1ServiceSpecMock({"key": "value"}),
                )
            ],
            V1ListMetaMock(),
        )
        self.k8s_client_mock.list_namespaced_service.return_value = (
            k8s_response
        )
        res = next(self.namespaced_collector.collect(), None)
        self.check_result(res, k8s_response)

    def test_all_namespaces_limit(self):
        k8s_response_1 = ServiceListResponseMock(
            [
                V1ServiceMock(
                    V1ObjectMetaMock(
                        f"name_{i}", f"namespace_{i}", f"uid_{i}"
                    ),
                    V1ServiceSpecMock({f"key_{i}": f"value_{i}"}),
                )
                for i in range(DEFAULT_LIMIT)
            ],
            V1ListMetaMock("token"),
        )
        k8s_response_2 = ServiceListResponseMock(
            [
                V1ServiceMock(
                    V1ObjectMetaMock(
                        f"name_{i}", f"namespace_{i}", f"uid_{i}"
                    ),
                    V1ServiceSpecMock({f"key_{i}": f"value_{i}"}),
                )
                for i in range(DEFAULT_LIMIT, DEFAULT_LIMIT * 2)
            ],
            V1ListMetaMock(),
        )
        self.k8s_client_mock.list_service_for_all_namespaces.side_effect = (
            k8s_response_1,
            k8s_response_2,
        )
        res = next(self.collector.collect(), None)
        k8s_response_1.items.extend(k8s_response_2.items)
        self.check_result(res, k8s_response_1)

    def test_namespaced_limit(self):
        k8s_response_1 = ServiceListResponseMock(
            [
                V1ServiceMock(
                    V1ObjectMetaMock(
                        f"name_{i}", f"namespace_{i}", f"uid_{i}"
                    ),
                    V1ServiceSpecMock({f"key_{i}": f"value_{i}"}),
                )
                for i in range(DEFAULT_LIMIT)
            ],
            V1ListMetaMock("token"),
        )
        k8s_response_2 = ServiceListResponseMock(
            [
                V1ServiceMock(
                    V1ObjectMetaMock(
                        f"name_{i}", f"namespace_{i}", f"uid_{i}"
                    ),
                    V1ServiceSpecMock({f"key_{i}": f"value_{i}"}),
                )
                for i in range(DEFAULT_LIMIT, DEFAULT_LIMIT * 2)
            ],
            V1ListMetaMock(),
        )
        self.k8s_client_mock.list_namespaced_service.side_effect = (
            k8s_response_1,
            k8s_response_2,
        )
        res = next(self.namespaced_collector.collect(), None)
        k8s_response_1.items.extend(k8s_response_2.items)
        self.check_result(res, k8s_response_1)
