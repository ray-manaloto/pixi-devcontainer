variable "REGISTRY" { default = "ghcr.io/my-org/cpp" }
variable "CONFIG_HASH" { default = "local" }
# Renovate will update these SHA digests automatically
variable "DIGEST_FOCAL" { default = "latest" }
variable "DIGEST_NOBLE" { default = "latest" }

group "default" { targets = ["image", "artifacts"] }

target "base" {
  dockerfile = "docker/Dockerfile"
  platforms  = ["linux/amd64"]
  cache-from = ["type=gha"]
  cache-to   = ["type=gha,mode=max"]
}

target "secure" {
  inherits = ["base"]

  # 🔒 Attestations: SBOM + Provenance
  attest = [
    "type=provenance,mode=min",
    "type=sbom"
  ]
}

target "image" {
  inherits = ["secure"]
  target   = "runtime"
  matrix = {
    # 20.04 (Focal) and 24.04 (Noble)
    os  = ["focal", "noble"]
    env = ["stable"]
  }
  name = "image-${os}-${env}"
  args = {
    # Select base image digest dynamically
    BASE_IMAGE = os == "focal" ? "ghcr.io/prefix-dev/pixi:focal@${DIGEST_FOCAL}" : "ghcr.io/prefix-dev/pixi:noble@${DIGEST_NOBLE}"
    PIXI_ENV   = "${env}"
  }
  cache-from = ["type=gha,scope=build-${os}-${env}"]
  cache-to   = ["type=gha,mode=max,scope=build-${os}-${env}"]
  tags = [
    "${REGISTRY}:${os}-${env}-${CONFIG_HASH}",
    "${REGISTRY}:${os}-${env}-latest",
  ]
}

target "artifacts" {
  inherits = ["secure"]
  matrix = {
    os  = ["focal", "noble"]
    env = ["stable"]
  }
  name     = "artifact-${os}-${env}"
  target   = "export"
  args = {
    BASE_IMAGE = os == "focal" ? "ghcr.io/prefix-dev/pixi:focal@${DIGEST_FOCAL}" : "ghcr.io/prefix-dev/pixi:noble@${DIGEST_NOBLE}"
    PIXI_ENV   = "${env}"
  }
  cache-from = ["type=gha,scope=build-${os}-${env}"]
  cache-to   = ["type=gha,mode=max,scope=build-${os}-${env}"]
  output = ["type=local,dest=./dist/${os}-${env}"]
  # artifact export is arch-specific; keep amd64 only
  platforms = ["linux/amd64"]
  tags      = []
}
