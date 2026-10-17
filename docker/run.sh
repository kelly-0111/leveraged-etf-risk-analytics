#!/usr/bin/env bash
# Run a command in the pipeline image on this repository's data. Inputs are mounted read-only
# (data/processed, data/windows); container results go to data/outputs-docker and
# data/windows-docker, apart from native results. The memory limit is a budget to validate:
# the container gets no swap, and its cgroup memory.peak (which includes page cache) is printed
# after the command.
#
#   docker/run.sh                       # the test suite
#   docker/run.sh python -m etf_risk.spark_pipeline --windows data/windows/<snapshot>/<name> \
#       --out-root data/outputs-docker/windows
#
# Settings: ETF_RISK_IMAGE (default etf-risk:dev), ETF_RISK_MEMORY (default 2.5g).
#
# AI contribution: written with Claude Code (Opus 5.5).
set -euo pipefail
cd "$(dirname "$0")/.."

image=${ETF_RISK_IMAGE:-etf-risk:dev}
memory=${ETF_RISK_MEMORY:-2.5g}
image_id=$(docker image inspect --format '{{.Id}}' "$image")
mkdir -p data/outputs-docker data/windows-docker

mounts=()
for dir in processed windows; do
    mounts+=(--mount "type=bind,source=$PWD/data/$dir,target=/app/data/$dir,readonly")
done
for dir in outputs-docker windows-docker; do
    mounts+=(--mount "type=bind,source=$PWD/data/$dir,target=/app/data/$dir")
done

[ "$#" -gt 0 ] || set -- pytest
docker run --rm --memory "$memory" --memory-swap "$memory" "${mounts[@]}" \
    --env ETF_RISK_IMAGE_ID="$image_id" --env ETF_RISK_MEMORY_LIMIT="$memory" "$image" \
    sh -c '"$@"; status=$?
        if peak=$(cat /sys/fs/cgroup/memory.peak 2>/dev/null); then
            echo "container memory.peak (cgroup, includes page cache): $((peak / 1048576)) MiB; limit $ETF_RISK_MEMORY_LIMIT" >&2
        else
            echo "container memory.peak: not available" >&2
        fi
        exit $status' sh "$@"
