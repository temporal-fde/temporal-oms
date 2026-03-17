#!/bin/bash

echo "🌉 Port-forwarding Traefik to localhost:8080..."
echo "Apps API available at: http://localhost:8080/api"
echo ""
echo "Press Ctrl+C to stop"
echo ""

kubectl port-forward -n traefik svc/traefik 8080:80
