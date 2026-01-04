variable "REGISTRY" { default = "ghcr.io/my-org/cpp" }
variable "CONFIG_HASH" { default = "local" }
# Renovate will update these SHA digests automatically
variable "DIGEST_FOCAL" { default = "latest" }
variable "DIGEST_NOBLE" { default = "latest" }

group "default" { targets = ["build"] }

target "base" {
  dockerfile = "docker/Dockerfile"
  platforms = ["linux/amd64"]
  cache-from = ["type=gha"]
  cache-to   = ["type=gha,mode=max"]
}

target "secure" {
  inherits = ["base"]

  # 🔒 Attestations: SBOM + Provenance
  attest = [
    "type=provenance,mode=max",
    "type=sbom"
  ]
}

target "base-load" {
  inherits = ["base"]
  output = ["type=docker"]
}

target "build" {
  inherits = ["secure"]
  matrix = {
    # 20.04 (Focal) and 24.04 (Noble)
    os = ["focal", "noble"]
    env = ["stable"]
  }
  name = "${os}-${env}"
  args = {
    # Select base image digest dynamically
    BASE_IMAGE = os == "focal" ? "ghcr.io/prefix-dev/pixi:focal@${DIGEST_FOCAL}" : "ghcr.io/prefix-dev/pixi:noble@${DIGEST_NOBLE}"
    PIXI_ENV   = "${env}"
  }
  tags = ["${REGISTRY}:${os}-${env}-${CONFIG_HASH}"]
}

target "build-local" {
  inherits = ["base-load"]
  matrix = {
    # 20.04 (Focal) and 24.04 (Noble)
    os = ["focal", "noble"]
    env = ["stable"]
  }
  name = "${os}-${env}"
  args = {
    # Select base image digest dynamically
    BASE_IMAGE = os == "focal" ? "ghcr.io/prefix-dev/pixi:focal@${DIGEST_FOCAL}" : "ghcr.io/prefix-dev/pixi:noble@${DIGEST_NOBLE}"
    PIXI_ENV   = "${env}"
  }
  tags = ["${REGISTRY}:${os}-${env}-${CONFIG_HASH}"]
}
