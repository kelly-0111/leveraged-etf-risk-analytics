"""macOS's paging and swap counters, from `vm_stat` (docs/host-counters-correction.md).

Pageins counts requests for pages from a pager, file reads included; Pageouts the pages paged
out; Swapins and Swapouts the pages moved between the memory compressor and the swap files
(mach/vm_statistics.h). psutil's swap_memory().sin and .sout are, on macOS, Pageins and Pageouts
times the page size, not swap traffic, so neither consumer reads them as swap.

Used by the result-cache experiment's host sampler (cache_experiment.py) and by the recovery
harness's host readings (jobs/harness.py).

AI contribution: written with Claude Code (Opus 5.5) on 2026-10-27, moved out of
cache_experiment.py so that both consumers share it. Tested with tests/test_vmstat.py.
"""
from __future__ import annotations

import re

VM_COUNTERS = ("pageins", "pageouts", "swapins", "swapouts")


def parse_vm_stat(text: str) -> dict:
    """The page size and the cumulative Pageins, Pageouts, Swapins and Swapouts, in pages; None
    for any that `vm_stat` does not print."""
    size = re.search(r"page size of (\d+) bytes", text)

    def count(name: str) -> int | None:
        match = re.search(rf"^{name.capitalize()}:\s+(\d+)\.", text, re.MULTILINE)
        return int(match.group(1)) if match else None
    return {"page_size": int(size.group(1)) if size else None, **{name: count(name) for name in VM_COUNTERS}}


def vm_bytes(parsed: dict) -> dict:
    """pageins_bytes, pageouts_bytes, swapins_bytes and swapouts_bytes: each counter times the page
    size; None where the counter or the page size is missing."""
    size = parsed.get("page_size")
    return {f"{name}_bytes": None if size is None or parsed.get(name) is None else parsed[name] * size
            for name in VM_COUNTERS}
