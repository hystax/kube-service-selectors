#!/usr/bin/env python
import argparse
import logging
import os
import time

from collections import defaultdict
from dataclasses import dataclass

from kubernetes import client as k8s_client, config as k8s_config
from kubernetes.client import V1Service
from prometheus_client import start_http_server
from prometheus_client.core import (
    CounterMetricFamily,
    GaugeMetricFamily,
    REGISTRY,
)
from prometheus_client.samples import Sample

from typing import Dict, List, Optional, Tuple

from kube_service_selectors.utils import map_to_prometheus_labels

DEFAULT_LABELS = ("service", "namespace", "uid")
DEFAULT_LIMIT = 1000
DEFAULT_PORT = 30091
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "kubeconfig")
DEFAULT_TIMEOUT = 10
LOG = logging.getLogger()


@dataclass
class CollectorState:
    state: str
    count: int = 0


class ServiceSelectorsCollector:
    _METRIC_NAME = "kube_service_selectors"
    _DESCRIPTION = "Kubernetes services selectors"

    def __init__(
        self,
        k8s_cl: k8s_client.CoreV1Api,
        namespaces: Optional[List[str]] = None,
        timeout: Optional[int] = None,
    ):
        self.namespaces = namespaces or []
        self.k8s_client = k8s_cl
        self.timeout = timeout
        self.states_map = {
            True: CollectorState("succeeded"),
            False: CollectorState("failed"),
        }

    def _add_defaults(
        self,
        service: V1Service,
        label_keys: List[str],
        label_values: List[str],
    ) -> Tuple[List[str], List[str]]:
        for v in DEFAULT_LABELS:
            label_keys.append(v)
        label_values.append(service.metadata.name)
        label_values.append(service.metadata.namespace)
        label_values.append(service.metadata.uid)
        return label_keys, label_values

    def _extract(
        self, services: List[V1Service]
    ) -> Dict[Tuple[str], List[List[str]]]:
        res = defaultdict(list)
        for service in services:
            selector_data = service.spec.selector or {}
            selector_keys, selector_values = map_to_prometheus_labels(
                selector_data
            )
            selector_keys, selector_values = self._add_defaults(
                service, selector_keys, selector_values
            )
            res[tuple(selector_keys)].append(selector_values)
        return res

    def _collector_gauge(
        self, metrics_dict: Dict[Tuple[str], List[List[str]]]
    ) -> GaugeMetricFamily:
        gauge = GaugeMetricFamily(
            self._METRIC_NAME, self._DESCRIPTION, labels=DEFAULT_LABELS
        )
        for label_keys, label_data in metrics_dict.items():
            for label_values in label_data:
                gauge.samples.append(
                    Sample(
                        gauge.name,
                        dict(zip(label_keys, label_values)),
                        value=1,
                        timestamp=None,
                    )
                )
        return gauge

    def _collector_state_counter(
        self, succeeded: bool = True
    ) -> CounterMetricFamily:
        name = f"{self._METRIC_NAME}_total"
        description = f"{self._DESCRIPTION} collector workflow result"
        counter = CounterMetricFamily(name, description, labels=["result"])
        for k, v in self.states_map.items():
            if k == succeeded:
                v.count += 1
            counter.add_metric([v.state], v.count)
        return counter

    def collect(self):
        def _wrap_k8s_call(func, *args, **kwargs):
            result = []
            response = func(*args, **kwargs)
            result.extend(response.items)
            while response.metadata._continue:
                response = func(
                    *args, **kwargs, _continue=response.metadata._continue
                )
                result.extend(response.items)
            return result

        try:
            services = []
            if self.namespaces:
                for namespace in self.namespaces:
                    services.extend(
                        _wrap_k8s_call(
                            self.k8s_client.list_namespaced_service,
                            namespace,
                            limit=DEFAULT_LIMIT,
                            _request_timeout=self.timeout,
                        )
                    )
            else:
                services = _wrap_k8s_call(
                    self.k8s_client.list_service_for_all_namespaces,
                    limit=DEFAULT_LIMIT,
                    _request_timeout=self.timeout,
                )

            metrics = self._extract(services)
        except Exception:
            LOG.exception("Error while collecting %s", self._METRIC_NAME)
            yield self._collector_state_counter(succeeded=False)
        else:
            yield self._collector_gauge(metrics)
            yield self._collector_state_counter()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"server port"
    )
    parser.add_argument(
        "--namespaces",
        type=str,
        help="list of comma-separated namespaces "
        "(will be listed from all if not provided)",
        default="",
    )
    parser.add_argument(
        "--debug", type=bool, default=False, help="enable debug logging"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"kubernetes requests timeout",
    )
    parser.add_argument(
        "--kubeconfig",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help="kubernetes config file path. "
        "Service account will be used if config missing",
    )
    args = parser.parse_args()

    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)

    if os.path.exists(args.kubeconfig):
        k8s_config.load_kube_config(args.kubeconfig)
    else:
        LOG.debug("No %s found, trying incluster config", args.kubeconfig)
        k8s_config.load_incluster_config()

    arg_namespaces = list(map(lambda x: x.strip(), args.namespaces.split(",")))
    if arg_namespaces:
        LOG.debug("Target namespaces - %s", arg_namespaces)
    else:
        LOG.debug("No namespaces specified. Will handle all available")
    collector = ServiceSelectorsCollector(
        k8s_client.CoreV1Api(), namespaces=arg_namespaces, timeout=args.timeout
    )
    REGISTRY.register(collector)

    LOG.info("Starting server...")
    start_http_server(args.port)
    LOG.info("Server started on port %s", args.port)

    while True:
        time.sleep(5)
