#!/usr/bin/env bash
# Build the pipeline image (local only; never push it). Records the commit and whether src/,
# pyproject.toml and uv.lock were clean, the same scope as code_state(). The build context is
# the working tree, so uncommitted changes there are included and recorded as not clean.
#
#   docker/build.sh [extra docker build options]     # image name: $ETF_RISK_IMAGE, default etf-risk:dev
#
# AI contribution: written with Claude Code (Opus 5.5).
set -euo pipefail
cd "$(dirname "$0")/.."

image=${ETF_RISK_IMAGE:-etf-risk:dev}
commit=$(git rev-parse HEAD)
if [ -z "$(git status --porcelain --untracked-files=all -- src pyproject.toml uv.lock)" ]; then
    clean=true
else
    clean=false
fi

# PySpark is locked as a 450 MB source archive; reuse this machine's uv cache entry for the
# locked version when present (see the pyspark-cache stage in the Dockerfile).
contexts=()
pyspark_version=$(awk '/^name = "pyspark"$/ { getline; gsub(/"/, "", $3); print $3; exit }' uv.lock)
pyspark_cache="$(uv cache dir 2>/dev/null || true)/sdists-v9/pypi/pyspark"
if [ -n "$pyspark_version" ] && [ -d "$pyspark_cache/$pyspark_version" ]; then
    contexts=(--build-context "pyspark-cache=$pyspark_cache")
    echo "reusing the uv cache entry for pyspark $pyspark_version"
fi

# ${a[@]+"${a[@]}"}: an empty array is an error under set -u in macOS's bash 3.2.
docker build ${contexts[@]+"${contexts[@]}"} --build-arg GIT_COMMIT="$commit" --build-arg GIT_WORKTREE_CLEAN="$clean" \
    --tag "$image" "$@" .
echo "built $image from $commit (src, pyproject.toml and uv.lock clean: $clean)"
