#!/bin/bash
# Render the repo as Argo CD does, validate it against the Kubernetes + Argo CD schemas, then check every app fence
# has exactly its own shape (scripts/fences.py). Needs kustomize, kubeconform, python3 with PyYAML.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf out && mkdir -p out
kustomize build . >out/meru.yaml
kubeconform -strict -summary \
  -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
  out/meru.yaml
python3 scripts/fences.py out/meru.yaml
