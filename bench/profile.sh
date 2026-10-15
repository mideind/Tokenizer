#!/usr/bin/env bash
# Profile a bench workload with the CPython 3.15+ sampling profiler
# (python -m profiling.sampling). Output goes to bench/out/ (gitignored).
#
#   bench/profile.sh [workload] [seconds]      # default: tokenize 15
#   PY=/path/to/python3.15 bench/profile.sh sentences 30
#
# Produces:
#   <workload>.pstats.txt   top functions/lines by self time
#   <workload>.self.txt     self time aggregated per function
#   <workload>.collapsed    collapsed stacks (input for other tools)
#   <workload>.flame.html   interactive flamegraph
#   <workload>.heatmap/     line-level heatmap of the source
#
# --blocking is essential here: the tokenizer is a deep chain of generators,
# and without stopping the process for each sample the profiler fails to
# unwind about 70% of stacks ("Error rate" in the pstats header), which
# misattributes the work of inner generators to the next() calls of outer ones.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
WORKLOAD="${1:-tokenize}"
SECONDS_="${2:-15}"
OUT="$HERE/out"
mkdir -p "$OUT"

if [[ -z "${PY:-}" ]]; then
    # A throwaway 3.15 venv with Tokenizer installed in editable mode
    VENV="$OUT/venv315"
    if [[ ! -x "$VENV/bin/python" ]]; then
        uv venv -q --python 3.15 "$VENV"
        VIRTUAL_ENV="$VENV" uv pip install -q -e "$HERE/.."
    fi
    PY="$VENV/bin/python"
fi

run() {
    "$PY" -m profiling.sampling run --blocking -r 2khz "$@" \
        "$HERE/bench.py" --loop "$WORKLOAD" -s "$SECONDS_"
}

run --sort tottime -l 40 > "$OUT/$WORKLOAD.pstats.txt"
grep -m1 "Error rate" "$OUT/$WORKLOAD.pstats.txt" || true
run --collapsed -o "$OUT/$WORKLOAD.collapsed"
run --flamegraph -o "$OUT/$WORKLOAD.flame.html"
run --heatmap -o "$OUT/$WORKLOAD.heatmap"

# Self time per function, from the leaf frames of the collapsed stacks
"$PY" - "$OUT/$WORKLOAD.collapsed" > "$OUT/$WORKLOAD.self.txt" <<'EOF'
import collections, re, sys
self_n: collections.Counter[str] = collections.Counter()
total = 0
for line in open(sys.argv[1]):
    stack, n = line.rsplit(" ", 1)
    total += int(n)
    self_n[re.sub(r":\d+$", "", stack.split(";")[-1])] += int(n)
for fn, n in self_n.most_common(30):
    print(f"{n / total * 100:5.1f}%  {fn}")
EOF
cat "$OUT/$WORKLOAD.self.txt"
echo "Output in $OUT/"
