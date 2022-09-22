Kubernetes services selectors exporter
====
Exports Kubernetes services selectors as metrics.

Uses Kubernetes API to collect services info.

[Source Code](https://github.com/hystax/kube-service-selectors) | [Docker Image](https://hub.docker.com/r/hystax/kube-service-selectors) | [Helm chart](https://github.com/hystax/helm-charts/tree/main/charts/kube-service-selectors)

## Metrics description
| Metric name| Metric type | Description | Labels/tags |
| ---------- | ----------- | ----------- | ----------- |
| kube_service_selectors | Gauge | Kubernetes selectors converted to Prometheus labels | `service`=&lt;service-name&gt; <br> `namespace`=&lt;service-namespace&gt; <br> `uid`=&lt;service-uid&gt; <br> `label_SELECTOR_LABEL`=&lt;SELECTOR_LABEL&gt; |
| kube_service_selectors_total | Counter | Counted exporter workflow result (succeeded and failed) | `result`=&lt;result&gt; |

kube_service_selectors transforms Kubernetes labels according to [Prometheus labels naming convention](https://prometheus.io/docs/concepts/data_model/#metric-names-and-labels) and resolves possible conflicts in [kube-state-metrics](https://github.com/kubernetes/kube-state-metrics/blob/master/README.md#conflict-resolution-in-label-names) way.

## Usage
```
usage: main.py [-h] [--port PORT] [--namespaces NAMESPACES] [--debug DEBUG]
               [--timeout TIMEOUT] [--kubeconfig KUBECONFIG]

optional arguments:
  -h, --help            show this help message and exit
  --port PORT           server port
  --namespaces NAMESPACES
                        list of comma-separated namespaces (will be listed
                        from all if not provided)
  --debug DEBUG         enable debug logging
  --timeout TIMEOUT     kubernetes requests timeout
  --kubeconfig KUBECONFIG
                        kubernetes config file path. Service account will be
                        used if config missing
```

### From source
The exporter requires Python 3.6 or above and Pip 3 to install requirements:
```bash
> pip3 install -r requirements.txt
```
By default server listens on 30091. Kubernetes config should be placed behind executable with `kubeconfig` name or passed as `--kubeconfig` argument when running outside Kubernetes:
```bash
> PYTHONPATH=.. python3 main.py --kubeconfig <kubeconfig_path>
```

### Using Docker
```bash
> docker run -d -v <kubeconfig_path>:/usr/src/app/kube_service_selectors/kubeconfig -p 30091:30091 --name kss_exporter  hystax/kube-service-selectors
```
