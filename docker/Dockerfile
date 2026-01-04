# checkov:skip=CKV_DOCKER_7: Base image is pinned via digests in bake file
# checkov:skip=CKV_DOCKER_2: Healthcheck handled downstream
# checkov:skip=CKV_DOCKER_3: Base image defines user
# syntax=docker/dockerfile:1
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /app

# 1. Install Dependencies
COPY pixi.toml pixi.lock ./

ARG PIXI_ENV=stable
# ⚡️ CACHE MOUNT: Persist downloads to host (10x faster)
RUN --mount=type=cache,target=/root/.cache/pixi \
    --mount=type=cache,target=/root/.cache/uv \
    pixi install --frozen --environment "${PIXI_ENV}" && \
    # 2. Freeze Environment (Pythonic Activation)
    pixi run -e "${PIXI_ENV}" python -c "import os, json; print(json.dumps(dict(os.environ)))" > /app/pixi_env.json && \
    # 3. Create Stable Entrypoint Link
    ln -sf "/app/.pixi/envs/${PIXI_ENV}/bin/python" /app/python_runtime && \
    # 4. Generate Portable Pack (S3 Artifact)
    PIXIPACK_PLATFORM="${PIXIPACK_PLATFORM:-linux-64}" pixi global install pixi-pack && \
    (pixi-pack -e "${PIXI_ENV}" --platform "${PIXIPACK_PLATFORM}" --use-cache /root/.cache/pixi --output-file /app/environment.tar.gz /app || \
     (echo "⚠️ pixi-pack failed, falling back to tarball copy" >&2 && tar -czf /app/environment.tar.gz -C "/app/.pixi/envs/${PIXI_ENV}" .))

COPY docker/entrypoint.py /app/entrypoint.py

USER 65532

ENTRYPOINT ["/app/python_runtime", "/app/entrypoint.py"]
CMD ["/bin/bash"]
