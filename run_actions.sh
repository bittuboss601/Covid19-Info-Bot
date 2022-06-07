#!/bin/bash

{
  banner "${PWD##*/}"
} || {
  echo "Unable to print banner"
}

echo "Starting action server"

echo "$Python environment path: ${ENVIRONMENT_SOURCE}"
echo "Activating python environment"
source "${ENVIRONMENT_SOURCE}"
echo "Activated python environment"

echo "Changing to agent directory"
cd "${AGENTS_BASE_DIR}/${PWD##*/}" || exit
echo "Now in directory: ${PWD}"

echo "Extracting port number from endpoints.yml"
PORT=$(< endpoints.yml sed -n -e 's/.localhost:\([0-9]\{4\}\).*/\1/p' | sed -n -e 's/.*\([0-9]\{4\}\).*/\1/p')
echo "Port Number: ${PORT}"

echo "run actions -p ${PORT} --debug"
rasa run actions -p "$PORT" --debug
