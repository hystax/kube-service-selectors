#!/usr/bin/env bash
set -e

TEST_IMAGE=kube-service-selectors-tests:build

docker build -t ${TEST_IMAGE} -f Dockerfile_tests .

echo "Black check>>>"
docker run -i --entrypoint black --rm ${TEST_IMAGE} --check .
echo "<<<Black check"

echo "PEP8 tests>>>"
docker run -i --entrypoint pycodestyle --rm ${TEST_IMAGE} --show-pep8 .
echo "<<<PEP8 tests"

echo "Nose tests>>>"
docker run -i -v $PWD/reports:/usr/src/app/kube_service_selectors/reports \
  --entrypoint nose2 --rm ${TEST_IMAGE}
echo "<<Nose tests"

docker rmi ${TEST_IMAGE}
