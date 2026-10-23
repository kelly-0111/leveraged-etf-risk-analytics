"""What an analysis job runs, and the inputs it names (spec §11).

JobParams says which windows → spark_pipeline → verify run makes the job's result:
- the snapshot, a folder under the worker's processed-data root;
- the window kind, window length, stride and anchor;
- the ticker that verify samples.

Unknown keys are refused, and so is a rolling stride below the CLI's minimum
(windows.MIN_STRIDE), since a job has no --allow-dense-stride. Tickers come from the snapshot,
and the leverages are fixed (1x and 2x). The processed-data and output roots are the worker's
settings, not the job's: the input checksums are what tie a job to its data.

input_checksums() is what submit records with the job, and what the worker checks again
before step 1. It hashes each daily-returns file and quality_report.json, the files windows.py
records in its config's inputs_sha256. A mismatch fails the attempt for good, since the job
names inputs that are no longer there.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_params.py.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, fields
from datetime import date
from pathlib import Path

from etf_risk.ingest import sha256_file
from etf_risk.windows import DEFAULT_ANCHOR, KIND_NAMES, MIN_STRIDE, ROLLING_WINDOW_DAYS, default_name

_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_TICKER = re.compile(r"[A-Z0-9][A-Z0-9.^-]{0,15}")


class InvalidParams(ValueError):
    """The job's parameters or its inputs cannot make a run; running again cannot help."""


@dataclass(frozen=True)
class JobParams:
    snapshot: str
    kind: str
    window_days: int = ROLLING_WINDOW_DAYS
    stride: int = MIN_STRIDE
    anchor: str = DEFAULT_ANCHOR
    sample_ticker: str = "AAPL"

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot, str) or not _NAME.fullmatch(self.snapshot) or ".." in self.snapshot:
            raise InvalidParams(f"snapshot must be a plain folder name, not {self.snapshot!r}")
        if self.kind not in KIND_NAMES:
            raise InvalidParams(f"kind must be one of {sorted(KIND_NAMES)}, not {self.kind!r}")
        for name in ("window_days", "stride"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise InvalidParams(f"{name} must be a positive integer, not {value!r}")
        if self.kind == "rolling" and self.stride < MIN_STRIDE:
            raise InvalidParams(f"a job's stride must be at least {MIN_STRIDE} (there is no --allow-dense-stride)")
        try:
            date.fromisoformat(self.anchor)
        except (TypeError, ValueError):
            raise InvalidParams(f"anchor must be an ISO date, not {self.anchor!r}") from None
        if not isinstance(self.sample_ticker, str) or not _TICKER.fullmatch(self.sample_ticker):
            raise InvalidParams(f"sample_ticker must be a ticker symbol, not {self.sample_ticker!r}")

    @classmethod
    def from_dict(cls, data: dict) -> JobParams:
        if not isinstance(data, dict):
            raise InvalidParams(f"job parameters must be an object, not {type(data).__name__}")
        unknown = set(data) - {f.name for f in fields(cls)}
        if unknown:
            raise InvalidParams(f"unknown job parameters: {', '.join(sorted(unknown))}")
        try:
            return cls(**data)
        except TypeError as error:
            raise InvalidParams(str(error)) from None

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def windows_name(self) -> str:
        """The windows folder name, as windows.py names it by default."""
        return default_name(self.kind, self.window_days, self.stride)


def input_checksums(processed_root: str | Path, snapshot: str) -> dict[str, str]:
    """SHA-256 of each file in the snapshot that windows.py reads, keyed by its path relative
    to the snapshot folder, as windows.py's config keys them."""
    snapshot_dir = Path(processed_root) / snapshot
    files = sorted((snapshot_dir / "daily_returns").glob("*.parquet"))
    if not files:
        raise InvalidParams(f"{snapshot_dir}: no daily returns")
    files.append(snapshot_dir / "quality_report.json")
    if not files[-1].is_file():
        raise InvalidParams(f"{snapshot_dir}: no quality_report.json")
    return {path.relative_to(snapshot_dir).as_posix(): sha256_file(path) for path in files}


def check_inputs(processed_root: str | Path, snapshot: str, recorded: dict[str, str]) -> None:
    """Raise InvalidParams unless the snapshot's files are exactly those the job recorded."""
    current = input_checksums(processed_root, snapshot)
    if current != recorded:
        changed = sorted(k for k in current.keys() & recorded.keys() if current[k] != recorded[k])
        raise InvalidParams("the job's inputs changed since it was submitted:"
                            + (f" changed {changed}" if changed else "")
                            + (f" missing {sorted(recorded.keys() - current.keys())}" if recorded.keys() - current.keys() else "")
                            + (f" new {sorted(current.keys() - recorded.keys())}" if current.keys() - recorded.keys() else ""))
