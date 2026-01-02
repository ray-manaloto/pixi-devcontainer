# syntax=docker/dockerfile:1
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /app

# 1. Install Dependencies
ARG PIXI_ENV
ARG PIXIPACK_PLATFORM
# ⚡️ CACHE MOUNT: Persist downloads to host
RUN --mount=type=bind,source=.,target=/src,readonly \
    --mount=type=cache,target=/root/.cache/pixi \
    --mount=type=cache,target=/root/.cache/uv \
    cp /src/pixi.toml /app/pixi.toml && \
    if [ -f /src/pixi.lock ]; then \
        cp /src/pixi.lock /app/pixi.lock && PIXI_FROZEN="--frozen"; \
    else \
        echo "pixi.lock not found; proceeding without --frozen" && PIXI_FROZEN=""; \
    fi && \
    pixi install ${PIXI_FROZEN} --environment ${PIXI_ENV}

# 2. Freeze Environment (Pythonic Activation)
# Dump env vars to JSON to bypass slow shell activation scripts
RUN pixi run -e ${PIXI_ENV} python -c "import os, json; print(json.dumps(dict(os.environ)))" > /app/pixi_env.json

# 3. Create Stable Entrypoint Link
# Docker ENTRYPOINT instructions cannot expand ARGs.
# We symlink the dynamic path to a static one (/app/python_runtime).
RUN ln -sf /app/.pixi/envs/${PIXI_ENV}/bin/python /app/python_runtime

# 4. Generate Portable Pack (S3 Artifact for Remote Server)
# pixi-pack requires pixi.toml to exist; generate pack if available
# Map docker TARGETPLATFORM to conda platform; allow override via PIXIPACK_PLATFORM
RUN pixi global install pixi-pack && \
    TARGET="${PIXIPACK_PLATFORM:-${TARGETPLATFORM:-linux/amd64}}" && \
    case "${TARGET}" in \
      linux/amd64) PACK_PLATFORM="linux-64" ;; \
      linux/arm64) PACK_PLATFORM="linux-aarch64" ;; \
      *) PACK_PLATFORM="" ;; \
    esac && \
    if [ -n "${PACK_PLATFORM}" ]; then \
      pixi-pack pack /app -e ${PIXI_ENV} --platform ${PACK_PLATFORM} -o /app/environment.tar.gz; \
    else \
      echo "pixi-pack skipped (unsupported platform ${TARGET})"; \
    fi || echo "pixi-pack skipped (optional)"

COPY docker/entrypoint.py /app/entrypoint.py

# Execute entrypoint using the symlinked python
ENTRYPOINT ["/app/python_runtime", "/app/entrypoint.py"]
CMD ["/bin/bash"]
