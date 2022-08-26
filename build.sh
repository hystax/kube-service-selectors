#!/usr/bin/env bash
set -e

OUTPUT=kube-service-selectors:build
docker build -t ${OUTPUT} --label commit=$(git rev-parse HEAD) --label version=${VERSION:-'none'} .