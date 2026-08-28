#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYPROJECT="$ROOT_DIR/pyproject.toml"
REQUIREMENTS="$ROOT_DIR/requirements/requirements.txt"

BUILDER_IMAGE="${SDIFF_LOCK_BUILDER_IMAGE:-241863724951.dkr.ecr.us-east-1.amazonaws.com/accounts-builder:focal-fossa-amd64-latest}"
PYPICLOUD_HOST="${SDIFF_LOCK_PYPICLOUD_HOST:-pypicloud.getkeepsafe.local}"
PYPICLOUD_IP="${SDIFF_LOCK_PYPICLOUD_IP:-}"

usage() {
  cat <<'EOF'
Usage: utils/update_sdiff_requirements.sh [--check]

Compare the exact sdiff pin in pyproject.toml with
requirements/requirements.txt. With no arguments, update a stale deployment
lock using the Linux builder.

Options:
  --check  Report a stale lock and exit 1 without changing files.
  -h, --help
           Show this help.

Environment overrides:
  SDIFF_LOCK_BUILDER_IMAGE   Linux builder image to run.
  SDIFF_LOCK_PYPICLOUD_HOST Internal package-index hostname.
  SDIFF_LOCK_PYPICLOUD_IP   Resolved index IP to pass to Docker.
EOF
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

extract_pyproject_pin() {
  sed -n 's/^[[:space:]]*"sdiff==\([^"[:space:]]*\)"[[:space:]]*,\{0,1\}[[:space:]]*$/\1/p' "$PYPROJECT"
}

extract_requirements_pin() {
  sed -n 's/^sdiff==\([^[:space:]\\]*\).*/\1/p' "$1"
}

mode="update"
case "${1:-}" in
  "") ;;
  --check) mode="check" ;;
  -h|--help)
    usage
    exit 0
    ;;
  *)
    usage >&2
    fail "Unknown argument: $1"
    ;;
esac

[[ "$#" -le 1 ]] || {
  usage >&2
  fail "Only one argument is supported."
}

[[ -f "$PYPROJECT" ]] || fail "Missing $PYPROJECT"
[[ -f "$REQUIREMENTS" ]] || fail "Missing $REQUIREMENTS"

pyproject_pin="$(extract_pyproject_pin)"
requirements_pin="$(extract_requirements_pin "$REQUIREMENTS")"

[[ -n "$pyproject_pin" ]] || fail "Expected one exact sdiff== pin in $PYPROJECT"
[[ "$pyproject_pin" != *$'\n'* ]] || fail "Found multiple exact sdiff pins in $PYPROJECT"
[[ -n "$requirements_pin" ]] || fail "Expected one sdiff== entry in $REQUIREMENTS"
[[ "$requirements_pin" != *$'\n'* ]] || fail "Found multiple sdiff entries in $REQUIREMENTS"

if [[ "$pyproject_pin" == "$requirements_pin" ]]; then
  echo "sdiff requirements are up to date: $pyproject_pin"
  exit 0
fi

echo "sdiff requirements are stale:"
echo "  pyproject.toml:                 $pyproject_pin"
echo "  requirements/requirements.txt: $requirements_pin"

if [[ "$mode" == "check" ]]; then
  exit 1
fi

require_command docker
require_command dig

docker info >/dev/null 2>&1 || fail "Docker is not running or is not accessible."
docker image inspect "$BUILDER_IMAGE" >/dev/null 2>&1 || fail \
  "Builder image is missing: $BUILDER_IMAGE. Build it from the ansible builder directory with 'make focal-fossa-local'."

if [[ -z "$PYPICLOUD_IP" ]]; then
  PYPICLOUD_IP="$(dig +short "$PYPICLOUD_HOST" | awk '/^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/ { print; exit }')"
fi
[[ -n "$PYPICLOUD_IP" ]] || fail \
  "Could not resolve $PYPICLOUD_HOST. Connect to the VPN or set SDIFF_LOCK_PYPICLOUD_IP."

lock_tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/content-validator-sdiff-lock.XXXXXX")"
cleanup() {
  rm -rf -- "$lock_tmp_dir"
}
trap cleanup EXIT

mkdir -p "$lock_tmp_dir/20.04"
cp "$REQUIREMENTS" "$lock_tmp_dir/20.04/requirements.txt"
chmod -R a+rwX "$lock_tmp_dir"

echo "Updating sdiff to $pyproject_pin in the Linux deployment lock..."
docker run \
  --user keepsafe-builder \
  --platform linux/amd64 \
  --add-host "$PYPICLOUD_HOST:$PYPICLOUD_IP" \
  -e "PYPICLOUD_HOST=$PYPICLOUD_HOST" \
  -v "$ROOT_DIR:/builder/source:ro" \
  -v "$lock_tmp_dir:/dist" \
  --rm \
  "$BUILDER_IMAGE" \
  bash -lc '
    set -euo pipefail

    python3.11 -m venv /tmp/lock-venv
    source /tmp/lock-venv/bin/activate

    pip install -q -U \
      "pip>=24.0,<26.0" \
      "pip-tools==7.5.3" \
      "setuptools>=61.0"

    echo "Compile toolchain: $(pip --version); $(pip-compile --version)"
    cd /builder/source

    pip-compile \
      --upgrade-package sdiff \
      --reuse-hashes \
      --trusted-host "$PYPICLOUD_HOST" \
      --index-url "http://$PYPICLOUD_HOST/simple/" \
      --generate-hashes \
      --strip-extras \
      --annotate \
      --annotation-style line \
      --output-file /dist/20.04/requirements.txt

    if ! grep -qx -- "--require-hashes" /dist/20.04/requirements.txt; then
      sed -i "/^--trusted-host/a --require-hashes" /dist/20.04/requirements.txt
    fi
  '

generated_requirements="$lock_tmp_dir/20.04/requirements.txt"
generated_pin="$(extract_requirements_pin "$generated_requirements")"

[[ "$generated_pin" == "$pyproject_pin" ]] || fail \
  "Generated lock contains sdiff==$generated_pin; expected sdiff==$pyproject_pin."
[[ "$(grep -c -x -- '--require-hashes' "$generated_requirements")" -eq 1 ]] || fail \
  "Generated lock must contain exactly one --require-hashes directive."
grep -qx -- "--index-url http://$PYPICLOUD_HOST/simple/" "$generated_requirements" || fail \
  "Generated lock must use pypicloud as its package index."
if grep -qE '(^--extra-index-url|git\+|pypi\.org)' "$generated_requirements"; then
  fail "Generated lock must not contain public-index or VCS dependency references."
fi

echo
echo "Generated requirements diff:"
diff_status=0
diff -u "$REQUIREMENTS" "$generated_requirements" || diff_status=$?
[[ "$diff_status" -le 1 ]] || fail "Could not compare the generated requirements file."

cp "$generated_requirements" "$REQUIREMENTS"
git -C "$ROOT_DIR" diff --check -- requirements/requirements.txt

echo
echo "Updated requirements/requirements.txt to sdiff==$pyproject_pin."
echo "Review with: git diff -- pyproject.toml requirements/requirements.txt"
