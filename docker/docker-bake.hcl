variable "REGISTRY" { default = "ghcr.io/my-org/cpp" }
variable "CONFIG_HASH" { default = "local" }
# Injected by build.py
variable "DIGEST_FOCAL" { default = "latest" }
variable "DIGEST_NOBLE" { default = "latest" }

group "default" { targets = ["build"] }

target "base" {
  dockerfile = "docker/Dockerfile"
  platforms = ["linux/amd64"]
  # ⚡️ GHA Layer Caching
  cache-from = ["type=gha"]
  cache-to   = ["type=gha,mode=max"]

  # 🔒 Supply Chain Security: Attestations
  attest = [
    "type=provenance,mode=max",
    "type=sbom"
  ]
}

target "build" {
  inherits = ["base"]

  matrix = {
    # 2 OSs x 1 Compiler Env = 2 Images (Bleeding edge GCC/LLVM)
    os = ["focal", "noble"]   # Ubuntu 20.04, 24.04
    env = ["stable"]
  }

  name = "${os}-${env}"

  args = {
    # Dynamically select base image digest (Security)
    BASE_IMAGE = "ghcr.io/prefix-dev/pixi:${os}@${os == "focal" ? DIGEST_FOCAL : DIGEST_NOBLE}"
    PIXI_ENV   = "${env}"
  }

  tags = [
    "${REGISTRY}:${os}-${env}-${CONFIG_HASH}",
    "${REGISTRY}:${os}-${env}-latest"
  ]
}
