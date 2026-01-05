# checkov:skip=CKV_DOCKER_7: Base image is pinned via digests in bake file
# checkov:skip=CKV_DOCKER_2: Healthcheck handled downstream
# checkov:skip=CKV_DOCKER_3: Base image defines user
# syntax=docker/dockerfile:1

ARG BASE_IMAGE

FROM ${BASE_IMAGE} AS builder
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
WORKDIR /app

# Copy manifests first for better cache reuse
COPY pixi.toml pixi.lock ./

ARG PIXI_ENV=stable
ARG PIXIPACK_PLATFORM=linux-64

# Install environment and generate pack
RUN --mount=type=cache,target=/root/.cache/pixi,sharing=locked \
    --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    set -euo pipefail && \
    pixi install --frozen --environment "${PIXI_ENV}" && \
    pixi run -e "${PIXI_ENV}" python -c "import os, json; print(json.dumps(dict(os.environ)))" > /app/pixi_env.json && \
    ln -sf "/app/.pixi/envs/${PIXI_ENV}/bin/python" /app/python_runtime && \
    pixi global install pixi-pack && \
    pixi-pack -e "${PIXI_ENV}" --platform "${PIXIPACK_PLATFORM}" --use-cache /root/.cache/pixi --output-file /app/environment.tar.gz /app

# Export-only stage for BuildKit local outputs
FROM scratch AS export
COPY --from=builder /app/environment.tar.gz /

# Runtime image (used for devcontainer)
FROM ${BASE_IMAGE} AS runtime
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
WORKDIR /app

COPY --from=builder /app/.pixi /app/.pixi
COPY --from=builder /app/pixi_env.json /app/pixi_env.json
COPY --from=builder /app/python_runtime /app/python_runtime

# Late-bind entrypoint to reduce cache invalidation
COPY docker/entrypoint.py /app/entrypoint.py

USER 65532

ENTRYPOINT ["/app/python_runtime", "/app/entrypoint.py"]
CMD ["/bin/bash"]
