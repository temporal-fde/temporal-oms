#!/bin/bash

export KUBECONFIG=/tmp/kind-config.yaml

echo "🌉 Setting up port-forwards..."
echo "  Traefik at: http://localhost:8080"
echo "    - Apps API at: http://localhost:8080/api"
echo "    - Validations at: http://localhost:8080/api/validations"
echo "  Processing API direct at: http://localhost:8081"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Forward Traefik (main ingress)
kubectl port-forward -n traefik svc/traefik 8080:80 &

# Forward Processing API service directly
kubectl port-forward -n temporal-oms-processing svc/processing-api 8081:80 &

# Wait for both to keep running
wait
