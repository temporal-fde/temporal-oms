Implemented exercises live in [workshop/README.md](workshop/README.md). Specs live under
[specs/workshop/](specs/workshop/).

1. Create `.env.local` if it does not already exist:
```sh
cp -n .env.codespaces .env.local
```
2. Follow the link your instructor gives you to get the command that updates `.env.local` with
`ANTHROPIC_API_KEY` and `OPENAI_API_KEY`. Alternatively, add your own values for those keys to
`.env.local`.
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
