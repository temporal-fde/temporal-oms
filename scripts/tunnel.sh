#!/bin/bash

export KUBECONFIG=/tmp/kind-config.yaml

echo "🌉 Setting up port-forwards..."
echo "  Apps API at:       http://localhost:8080  (host: localhost or api.local)"
echo "  Processing API at: http://localhost:8070  (host: localhost or processing-api.local)"
echo "  Enablements API at: http://localhost:8050"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Forward Traefik — web entrypoint (apps-api on :8080) and processing entrypoint (:8070)
kubectl port-forward -n traefik svc/traefik 8080:80 8070:8070 &
kubectl port-forward -n temporal-oms-enablements svc/enablements-api 8050:8050 &

# Wait for all forwards to keep running
wait
