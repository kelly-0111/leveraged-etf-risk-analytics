"""etf_risk.vmstat, the vm_stat parser that the result-cache experiment's host sampler and the
recovery harness's host readings share, and both consumers' use of it.

AI contribution: written with Claude Code (Opus 5.5) on 2026-10-27.
"""
import subprocess
import sys

import pytest

from etf_risk import cache_experiment as e3
from etf_risk import vmstat
from etf_risk.jobs import harness

VM_STAT = """Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                                4589.
Pages stored in compressor:             1172538.
Pageins:                               49262910.
Pageouts:                               1562003.
Swapins:                               80132854.
Swapouts:                              84015127.
"""


def test_the_page_size_and_the_four_counters_are_read_by_their_own_names():
    assert vmstat.parse_vm_stat(VM_STAT) == {"page_size": 16384, "pageins": 49262910, "pageouts": 1562003,
                                             "swapins": 80132854, "swapouts": 84015127}


def test_a_counter_vm_stat_does_not_print_is_none():
    assert vmstat.parse_vm_stat("") == dict.fromkeys(("page_size", *vmstat.VM_COUNTERS))
    assert vmstat.parse_vm_stat(VM_STAT.replace("Swapouts", "Swap outs"))["swapouts"] is None


def test_bytes_are_pages_times_the_page_size_and_none_without_either():
    assert vmstat.vm_bytes(vmstat.parse_vm_stat(VM_STAT)) == {
        "pageins_bytes": 49262910 * 16384, "pageouts_bytes": 1562003 * 16384,
        "swapins_bytes": 80132854 * 16384, "swapouts_bytes": 84015127 * 16384}
    assert set(vmstat.vm_bytes(vmstat.parse_vm_stat("")).values()) == {None}
    no_size = vmstat.parse_vm_stat(VM_STAT.replace("page size of 16384 bytes", "page size unknown"))
    assert set(vmstat.vm_bytes(no_size).values()) == {None}


def test_the_result_cache_experiment_uses_the_shared_parser():
    assert e3.parse_vm_stat is vmstat.parse_vm_stat and e3.VM_COUNTERS is vmstat.VM_COUNTERS


def test_the_recovery_harness_reads_the_counters_through_the_shared_parser(monkeypatch):
    seen = []
    real = vmstat.parse_vm_stat
    monkeypatch.setattr(vmstat, "parse_vm_stat", lambda text: seen.append(text) or real(text))
    state = harness.host_state(command=lambda *argv: VM_STAT if argv[0] == "vm_stat" else "")
    assert seen == [VM_STAT] and state["swapouts_bytes"] == 84015127 * 16384


@pytest.mark.skipif(sys.platform != "darwin", reason="vm_stat is macOS's")
def test_the_real_vm_stat_gives_every_counter():
    parsed = vmstat.parse_vm_stat(subprocess.run(["vm_stat"], capture_output=True, text=True, check=True).stdout)
    assert all(isinstance(parsed[k], int) for k in ("page_size", *vmstat.VM_COUNTERS))
