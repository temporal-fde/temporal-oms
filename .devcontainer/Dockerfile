FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ARG TARGETARCH
ARG TEMPORAL_CLI_VERSION=1.7.0
ARG UV_VERSION=0.11.6
ARG BUF_VERSION=1.46.0
ARG XH_VERSION=0.25.3
ARG KIND_VERSION=0.31.0
ARG K3D_VERSION=5.8.3
ARG K9S_VERSION=0.50.18

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      gpg \
      jq \
      lsof \
      procps \
      tar \
      unzip \
      xz-utils \
      yq \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) temporal_arch="amd64"; uv_arch="x86_64"; buf_arch="x86_64"; xh_arch="x86_64-unknown-linux-musl"; k9s_arch="amd64" ;; \
      arm64) temporal_arch="arm64"; uv_arch="aarch64"; buf_arch="aarch64"; xh_arch=""; k9s_arch="arm64" ;; \
      *) echo "unsupported TARGETARCH=${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    curl -fsSL "https://github.com/temporalio/cli/releases/download/v${TEMPORAL_CLI_VERSION}/temporal_cli_${TEMPORAL_CLI_VERSION}_linux_${temporal_arch}.tar.gz" \
      | tar -xz -C /usr/local/bin temporal; \
    chmod +x /usr/local/bin/temporal; \
    curl -fsSL "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-${uv_arch}-unknown-linux-gnu.tar.gz" \
      | tar -xz --strip-components=1 -C /usr/local/bin "uv-${uv_arch}-unknown-linux-gnu/uv" "uv-${uv_arch}-unknown-linux-gnu/uvx"; \
    curl -fsSL "https://github.com/bufbuild/buf/releases/download/v${BUF_VERSION}/buf-Linux-${buf_arch}" \
      -o /usr/local/bin/buf; \
    chmod +x /usr/local/bin/buf; \
    if [[ -n "${xh_arch}" ]]; then \
      curl -fsSL "https://github.com/ducaale/xh/releases/download/v${XH_VERSION}/xh-v${XH_VERSION}-${xh_arch}.tar.gz" \
        | tar -xz --strip-components=1 -C /usr/local/bin "xh-v${XH_VERSION}-${xh_arch}/xh"; \
      chmod +x /usr/local/bin/xh; \
    else \
      echo "Skipping xh install for TARGETARCH=${TARGETARCH}; GitHub Codespaces uses amd64."; \
    fi; \
    curl -fsSL "https://github.com/kubernetes-sigs/kind/releases/download/v${KIND_VERSION}/kind-linux-${temporal_arch}" \
      -o /usr/local/bin/kind; \
    chmod +x /usr/local/bin/kind; \
    curl -fsSL "https://github.com/k3d-io/k3d/releases/download/v${K3D_VERSION}/k3d-linux-${temporal_arch}" \
      -o /usr/local/bin/k3d; \
    chmod +x /usr/local/bin/k3d; \
    curl -fsSL "https://github.com/derailed/k9s/releases/download/v${K9S_VERSION}/k9s_Linux_${k9s_arch}.tar.gz" \
      | tar -xz -C /usr/local/bin k9s; \
    chmod +x /usr/local/bin/k9s

RUN temporal --version \
    && uv --version \
    && buf --version \
    && if command -v xh >/dev/null 2>&1; then xh --version; fi \
    && kind --version \
    && k3d version \
    && k9s version --short
