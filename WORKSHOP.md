Implemented exercises live in [workshop/README.md](workshop/README.md). Specs live under
[specs/workshop/](specs/workshop/).

1. Visit here to get access to keys: https://codeshare.io/2jEVPM
2. Check the `.env.local` is in your codespace and has API keys.
3. Start Temporal server
```sh
temporal server start-dev \
--ip 0.0.0.0 \
--port 7233 \
--ui-ip 0.0.0.0 \
--ui-port 8233
```
4. Set up your namespaces:
```
./scripts/setup-temporal-namespaces.sh
```
5. For Kubernetes: 
```sh
OVERLAY=local ./scripts/k3d/demo-up
```

Or, if k8s infra already exists:
```sh
OVERLAY=local ./scripts/k3d/app-deploy.sh
```
