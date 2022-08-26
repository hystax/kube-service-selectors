FROM python:3.9-slim
MAINTAINER Hystax

WORKDIR /usr/src/app/kube_service_selectors

ENV PYTHONPATH "${PYTHONPATH}:/usr/src/app"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY kube_service_selectors ./

ENTRYPOINT ["/usr/src/app/kube_service_selectors/main.py"]
