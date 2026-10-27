# Claude Code message 13

Session: `d50bcd16-34a8-45d0-8956-1e2da5d4b461` · prompt sent 2026-10-24 04:49 (local time)

Redacted record: [transcript.jsonl](transcript.jsonl)

This readable view includes user/assistant messages and tool calls/results. Internal reasoning and session metadata are omitted.

Redactions (markers like `[REDACTED:email]`; home directory shown as `~`): git-user ×3, home ×136, model-reasoning ×6, user ×22. Rules: `.claude/hooks/transcript_privacy.py`. The unredacted original stays local only.

## 1. User — 2026-10-24T09:49:15.806Z



<pasted_content id="8ce0">
While the isolated check is blocked, finish the readiness review in one batch.

Audit memory_check.py against the approved rules: restart-segment completeness, OOM/event baselines, leftover-process detection, cleanup ownership, and the distinction between container budgets and unapproved native targets. Report concrete discrepancies; avoid unrelated refactoring.

Prepare a short machine-preparation checklist, the exact run command, instructions for each failure exit, and an updated PR checklist showing completed and pending acceptance criteria.

Do not repeatedly rerun the same preflight or test suites. Keep services stopped until I confirm the machine is ready. Do not touch other projects or the M3 worktree.
</pasted_content id="8ce0">


## 2. Assistant — 2026-10-24T09:52:16.722Z

This is a review, not a fix. I'll read the committed tool and the compose file and report concrete discrepancies with line references. I'll check one read-only fact (whether this project already has Docker volumes), and I won't rerun the preflight or any tests. Reading the tool in full:

## 3. Assistant — 2026-10-24T09:52:17.880Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/worker-pipeline/tests/memory_check.py",
  "offset": 90,
  "limit": 160
}
```

## 4. User — 2026-10-24T09:52:18.197Z

### Tool result

```
90	    # one 2.7 GiB step tree (the host lock runs one at a time), 0.3 for the job processes and
91	    # pytest, 0.5 for both containers growing to their budgets, and 0.5 to spare
92	    "idle_available": 4 * GiB,
93	    "compressor_growth": 256 * MiB,
94	    "swap_growth": 256 * MiB,
95	}
96	# and supplementary thresholds, reported and never enforced: the containers' anon memory and limit
97	# hits, and the native-process targets ("step " and "process "), which are not approved budgets.
98	PROPOSED = {
99	    "mysql anon": 410 * MiB,          # 80% of its budget; 264 and 313 MiB after one and two runs (spec §11)
100	    "kafka anon": 512 * MiB,          # 80% of its budget, with a 256 MiB heap
101	    "mysql limit hits": 0,            # memory.events max during the run
102	    "kafka limit hits": 0,
103	    "step windows": 512 * MiB,        # 0.12 GiB in M2
104	    "step spark_pipeline": 3 * GiB,   # native stride 21 in the stride experiment: 2.62-2.73 GiB
105	    "step verify": 3 * GiB,           # a Spark session too; 0.45-0.58 GiB in M2
106	    "process worker": 128 * MiB,      # 63.0 MiB in M2
107	    "process reconciler": 128 * MiB,  # 51.6 MiB in M2
108	    "process submit": 128 * MiB,      # not measured before
109	}
110	NATIVE = ("step ", "process ")   # the prefixes of the native-process targets in PROPOSED
111	PORTS = (3307, 9094, 6380)
112	SETTLE_S = 30
113	SNAPSHOT = REPO / "data" / "processed" / "full-2026-10-12"   # what tests/test_jobs_live_pipeline.py reads
114	RUNS = (("suites", sorted(p.relative_to(REPO).as_posix() for p in (REPO / "tests").glob("test_jobs_*.py")), {}),
115	        ("acceptance", ["tests/test_jobs_live_pipeline.py"], {"ETF_RISK_LIVE_PIPELINE": "1"}))
116	TIMEOUTS = {"suites": 1800, "acceptance": 3600}
117	ROLES = ("worker", "reconciler", "submit")
118	VM_PROCESS = "com.apple.Virtualization.VirtualMachine"   # Docker Desktop's VM on Apple silicon
119	EVENTS = ("low", "high", "max", "oom", "oom_kill", "oom_group_kill")
120	KERNEL_PARTS = ("kernel_stack", "pagetables", "sec_pagetables", "percpu", "vmalloc", "slab")
121	CGROUP_SCRIPT = ('cd /sys/fs/cgroup && printf "peak %s\\nlimit %s\\ncurrent %s\\n" "$(cat memory.peak)" '
122	                 '"$(cat memory.max)" "$(cat memory.current)" && while read k v; do echo "stat_$k $v"; done '
123	                 '< memory.stat && while read k v; do echo "events_$k $v"; done < memory.events')
124	
125	
126	def now() -> str:
127	    return datetime.now(timezone.utc).isoformat()
128	
129	
130	def size(value: int | None) -> str:
131	    if value is None:
132	        return "-"
133	    return f"{value / GiB:.2f} GiB" if abs(value) >= GiB else f"{value / MiB:,.0f} MiB"
134	
135	
136	def largest(values: Iterable[int | None]) -> int | None:
137	    return max((v for v in values if v is not None), default=None)
138	
139	
140	# Containers
141	
142	def parse_cgroup(text: str) -> dict | None:
143	    """CGROUP_SCRIPT's output as one reading: the total peak, limit (None for "max") and current
144	    usage; anon, file and kernel memory (the sum of its parts on kernels without a kernel line);
145	    and the memory.events counters. None without a peak or an anon figure."""
146	    raw: dict[str, int | None] = {}
147	    for line in text.splitlines():
148	        key, _, value = line.strip().partition(" ")
149	        value = value.strip()
150	        if key and value == "max":
151	            raw[key] = None
152	        elif key and value.isdigit():
153	            raw[key] = int(value)
154	    if not isinstance(raw.get("peak"), int) or not isinstance(raw.get("stat_anon"), int):
155	        return None
156	    has_kernel = isinstance(raw.get("stat_kernel"), int)
157	    return {"peak": raw["peak"], "limit": raw.get("limit"), "current": raw.get("current"),
158	            "anon": raw["stat_anon"], "file": raw.get("stat_file"),
159	            "kernel": raw["stat_kernel"] if has_kernel else sum(raw.get(f"stat_{p}") or 0 for p in KERNEL_PARTS),
160	            "kernel_from": "kernel" if has_kernel else "parts",
161	            "events": {name: raw.get(f"events_{name}") or 0 for name in EVENTS}}
162	
163	
164	def read_cgroup(service: str, run: Callable = subprocess.run) -> dict | None:
165	    """One reading of the service container's cgroup; None while it cannot be read (paused,
166	    restarting, or docker failing)."""
167	    try:
168	        out = run(["docker", "compose", "-f", str(services.COMPOSE_FILE), "exec", "-T", service, "sh", "-c",
169	                   CGROUP_SCRIPT], capture_output=True, text=True, timeout=10)
170	    except (OSError, subprocess.TimeoutExpired):
171	        return None
172	    return parse_cgroup(out.stdout) if out.returncode == 0 else None
173	
174	
175	def segments(readings: Iterable[dict | None]) -> list[list[dict]]:
176	    """The readings of each life of a container, in time order. A restart can reset the
177	    counters, so a new segment starts wherever memory.peak or a memory.events counter goes
178	    down. A missing reading (paused, restarting) starts none."""
179	    lives: list[list[dict]] = []
180	    for r in readings:
181	        if r is None:
182	            continue
183	        last = lives[-1][-1] if lives else None
184	        if last is None or r["peak"] < last["peak"] or any(r["events"][k] < last["events"][k] for k in EVENTS):
185	            lives.append([])
186	        lives[-1].append(r)
187	    return lives
188	
189	
190	def summarize_container(readings: list[dict | None], budget: int) -> dict:
191	    """Per segment, and over the run. The first segment's events count from its first reading,
192	    taken as the run began; a later segment began with a restart during the run, and its
193	    counters count from zero."""
194	    parts = []
195	    for i, life in enumerate(segments(readings)):
196	        first, last = life[0], life[-1]
197	        base = first["events"] if i == 0 else dict.fromkeys(EVENTS, 0)
198	        parts.append({"readings": len(life), "from_utc": first.get("at_utc"), "to_utc": last.get("at_utc"),
199	                      "limit_bytes": last["limit"], "peak_bytes": max(r["peak"] for r in life),
200	                      **{f"{kind}_bytes": largest(r[kind] for r in life) for kind in ("anon", "file", "kernel")},
201	                      "events": {k: last["events"][k] - base[k] for k in EVENTS}})
202	    return {"budget_bytes": budget, "segments": parts,
203	            **{key: largest(s[key] for s in parts) for key in ("peak_bytes", "anon_bytes", "file_bytes", "kernel_bytes")},
204	            "events": {k: sum(s["events"][k] for s in parts) for k in EVENTS}}
205	
206	
207	# Host and processes
208	
209	def compressor_bytes(vm_stat: str) -> int:
210	    page = re.search(r"page size of (\d+) bytes", vm_stat)
211	    pages = re.search(r"Pages occupied by compressor:\s+(\d+)", vm_stat)
212	    if not page or not pages:
213	        raise ValueError("vm_stat: no page size or compressor line")
214	    return int(pages.group(1)) * int(page.group(1))
215	
216	
217	def host_memory() -> dict:
218	    vm_stat = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=10).stdout
219	    return {"available_bytes": psutil.virtual_memory().available, "compressor_bytes": compressor_bytes(vm_stat),
220	            "swap_bytes": psutil.swap_memory().used}
221	
222	
223	def available_memory() -> int:
224	    return psutil.virtual_memory().available
225	
226	
227	def role(cmdline: list[str] | None) -> str | None:
228	    """worker, reconciler or submit for `python -m etf_risk.jobs <role> ...`, pytest for `python -m pytest`."""
229	    if not cmdline or len(cmdline) < 3 or cmdline[1] != "-m":
230	        return None
231	    if cmdline[2] == "etf_risk.jobs":
232	        return cmdline[3] if len(cmdline) > 3 and cmdline[3] in ROLES else None
233	    return "pytest" if cmdline[2] == "pytest" else None
234	
235	
236	@dataclass(frozen=True)
237	class Seen:
238	    """A process as the sampler sees it; tests make their own."""
239	    key: tuple                      # (pid, create time): a pid reused by a new process is a new key
240	    pid: int
241	    name: str | None
242	    cmdline: Callable[[], list[str]]
243	    rss: Callable[[], int]
244	
245	
246	def live_processes() -> Iterable[Seen]:
247	    for proc in psutil.process_iter(["name", "create_time"]):
248	        yield Seen((proc.pid, proc.info["create_time"]), proc.pid, proc.info["name"], proc.cmdline,
249	                   lambda proc=proc: proc.memory_info().rss)
```

## 5. Assistant — 2026-10-24T09:52:20.593Z

### Tool call: Bash

```
{
  "command": "echo \"=== compose: volumes, restart policies, healthchecks\"; grep -n -E '^volumes:|^  [a-z-]+:$|^    volumes:|^      - [a-z-]+:/|restart:|mem_limit|memswap_limit' docker/compose.yaml; echo \"=== this project's Docker volumes now (read-only)\"; docker volume ls --filter label=com.docker.compose.project=etf-risk-jobs --format '{{.Name}}  created {{.CreatedAt}}' 2>&1 | head; echo \"(end)\"; echo \"=== this project's networks now\"; docker network ls --filter label=com.docker.compose.project=etf-risk-jobs --format '{{.Name}}' | head; echo \"(end)\"",
  "description": "Show compose volumes and policies, and this project's volumes"
}
```

## 6. User — 2026-10-24T09:52:25.220Z

### Tool result

```
=== compose: volumes, restart policies, healthchecks
25:  mysql:
32:    mem_limit: 512m
33:    memswap_limit: 512m
41:  kafka:
60:    mem_limit: 640m
61:    memswap_limit: 640m
=== this project's Docker volumes now (read-only)
(end)
=== this project's networks now
(end)
```

## 7. Assistant — 2026-10-24T09:52:46.177Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/worker-pipeline/tests/memory_check.py",
  "offset": 250,
  "limit": 300
}
```

## 8. User — 2026-10-24T09:52:46.298Z

### Tool result

```
250	
251	
252	class Sampler:
253	    """Two sampling threads, and what they keep: the largest of each figure, and the smallest
254	    available memory. Tests call sample_processes and sample_containers directly."""
255	
256	    def __init__(self, samples: Path, *, read_cgroup: Callable = read_cgroup, host_memory: Callable = host_memory,
257	                 processes: Callable = live_processes, available: Callable = available_memory,
258	                 clock: Callable = now, intervals: tuple[float, float] = (0.5, 5.0)):
259	        self.samples = samples
260	        self._read_cgroup, self._host_memory, self._processes = read_cgroup, host_memory, processes
261	        self._available, self._clock, self._intervals = available, clock, intervals
262	        self.rss = {name: 0 for name in (*ROLES, "pytest", "vm")}
263	        self.pids: dict[str, set[int]] = {name: set() for name in self.rss}
264	        self.available_min: int | None = None
265	        self.readings: dict[str, list[dict | None]] = {service: [] for service in services.SERVICES}
266	        self.host: list[dict] = []
267	        self.errors = 0
268	        self._roles: dict[tuple, str | None] = {}
269	        self._stopping = threading.Event()
270	        self._threads: list[threading.Thread] = []
271	
272	    def sample_processes(self) -> None:
273	        available = self._available()
274	        self.available_min = available if self.available_min is None else min(self.available_min, available)
275	        for seen in self._processes():
276	            if seen.key not in self._roles:      # a process's command line is read once
277	                try:
278	                    self._roles[seen.key] = "vm" if seen.name == VM_PROCESS else role(seen.cmdline())
279	                except (psutil.Error, OSError):
280	                    self._roles[seen.key] = None
281	            name = self._roles[seen.key]
282	            if name:
283	                try:
284	                    self.rss[name] = max(self.rss[name], seen.rss())
285	                except (psutil.Error, OSError):
286	                    continue
287	                self.pids[name].add(seen.pid)
288	
289	    def sample_containers(self) -> None:
290	        line: dict = {"at_utc": self._clock()}
291	        try:
292	            line.update(self._host_memory())
293	        except Exception as error:          # the containers are read all the same
294	            self._failed(error)
295	        for service in services.SERVICES:
296	            reading = self._read_cgroup(service)
297	            line[service] = reading = None if reading is None else {**reading, "at_utc": line["at_utc"]}
298	            self.readings[service].append(reading)
299	        line["rss_bytes"] = dict(self.rss)
300	        self.host.append(line)
301	        with self.samples.open("a") as out:
302	            out.write(json.dumps(line) + "\n")
303	
304	    def tick(self, sample: Callable[[], None]) -> None:
305	        """One sample. A failure is counted, the first three are reported, and sampling goes on."""
306	        try:
307	            sample()
308	        except Exception as error:
309	            self._failed(error)
310	
311	    def _failed(self, error: Exception) -> None:
312	        self.errors += 1
313	        if self.errors <= 3:
314	            print(f"sampler: {type(error).__name__}: {error}", file=sys.stderr)
315	
316	    def start(self) -> None:
317	        for sample, interval in zip((self.sample_processes, self.sample_containers), self._intervals):
318	            thread = threading.Thread(target=self._loop, args=(sample, interval), daemon=True)
319	            thread.start()
320	            self._threads.append(thread)
321	
322	    def stop(self) -> None:
323	        self._stopping.set()
324	        for thread in self._threads:
325	            thread.join()
326	
327	    def _loop(self, sample: Callable[[], None], interval: float) -> None:
328	        while not self._stopping.is_set():
329	            self.tick(sample)
330	            self._stopping.wait(interval)
331	
332	
333	# Records of the runs
334	
335	def launcher_peaks(root: Path) -> dict[str, int]:
336	    """The largest peak summed RSS per step over every launch under root, failed ones too."""
337	    peaks: dict[str, int] = {}
338	    for path in root.glob("**/logs/*.launcher.json"):
339	        step = path.name.removesuffix(".launcher.json")
340	        peaks[step] = max(peaks.get(step, 0), json.loads(path.read_text()).get("peak_rss_bytes") or 0)
341	    return peaks
342	
343	
344	def job_label(params: dict) -> str:
345	    return "calendar-year" if params["kind"] == "calendar-year" else f"{params['kind']}, stride {params['stride']}"
346	
347	
348	def job_peaks(root: Path) -> dict[str, dict[str, int]]:
349	    """Per kind of job and step, the largest peak over the attempts that wrote attempt.json."""
350	    peaks: dict[str, dict[str, int]] = {}
351	    for path in root.glob("**/attempt.json"):
352	        record = json.loads(path.read_text())
353	        job = peaks.setdefault(job_label(record["params"]), {})
354	        for step in record.get("steps", []):
355	            job[step["name"]] = max(job.get(step["name"], 0), step.get("peak_rss_bytes") or 0)
356	    return peaks
357	
358	
359	def keep_records(temp: Path, out: Path) -> None:
360	    """Copy the launchers' and attempts' records out of pytest's temporary folder."""
361	    for path in [*temp.glob("**/logs/*.launcher.json"), *temp.glob("**/attempt.json")]:
362	        target = out / path.relative_to(temp)
363	        target.parent.mkdir(parents=True, exist_ok=True)
364	        shutil.copy2(path, target)
365	
366	
367	def junit_counts(path: Path) -> dict:
368	    """The JUnit file's totals; readable is False when the file is missing or broken."""
369	    try:
370	        root = ET.parse(path).getroot()
371	    except (OSError, ET.ParseError):
372	        root = None
373	    suite = None if root is None else root if root.tag == "testsuite" else root.find("testsuite")
374	    if suite is None:
375	        return {"readable": False, "tests": 0, "failures": 0, "errors": 0, "skipped": 0}
376	    return {"readable": True, **{key: int(suite.get(key, 0)) for key in ("tests", "failures", "errors", "skipped")}}
377	
378	
379	# Running pytest, and what it leaves behind
380	
381	def run_bounded(command: list[str], *, cwd: Path, env: dict, log: Path, timeout: float, grace: float = 120) -> int | None:
382	    """A command in a session of its own, its output in log. Past timeout, or when this process
383	    is interrupted, the command gets SIGINT, so pytest runs its fixtures' teardown, and after
384	    grace its process group gets SIGKILL. The exit code, or None after a timeout."""
385	    with open(log, "w") as handle:
386	        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT,
387	                                   start_new_session=True)
388	        try:
389	            return process.wait(timeout=timeout)
390	        except subprocess.TimeoutExpired:
391	            interrupt(process, grace)
392	            return None
393	        except BaseException:
394	            interrupt(process, grace)
395	            raise
396	
397	
398	def interrupt(process: subprocess.Popen, grace: float) -> None:
399	    process.send_signal(signal.SIGINT)
400	    try:
401	        process.wait(timeout=grace)
402	    except subprocess.TimeoutExpired:
403	        pass
404	    try:
405	        os.killpg(process.pid, signal.SIGKILL)   # what is left of its group, the command included
406	    except (ProcessLookupError, PermissionError):
407	        pass
408	    process.wait()
409	
410	
411	def run_pytest(name: str, files: list[str], env: dict, out: Path, temp: Path, timeout: float) -> dict:
412	    """One pytest run, with its own temporary folder under temp, and its log and JUnit file in out."""
413	    junit = out / f"{name}.xml"
414	    command = [sys.executable, "-m", "pytest", *files, "-q", "-rs", "-p", "no:cacheprovider",
415	               "--basetemp", str(temp / name), "--junitxml", str(junit)]
416	    start = time.monotonic()
417	    code = run_bounded(command, cwd=REPO, env=env, log=out / f"{name}.log", timeout=timeout)
418	    return {"exit_code": code, "seconds": round(time.monotonic() - start, 1), **junit_counts(junit)}
419	
420	
421	def leftovers(temp: Path) -> list[psutil.Process]:
422	    """The processes that runs under temp left behind: those whose command line names temp
423	    (workers, reconcilers, launchers and steps), and those carrying the marker of a store whose
424	    outputs are under temp (the steps' JVMs and Python workers). No other process is touched."""
425	    me, folders = os.getpid(), {str(temp), str(temp.resolve())}
426	    stores = {path.name for path in temp.glob("*/*/out/*") if path.is_dir()}
427	    found: dict[int, psutil.Process] = {}
428	    for proc in psutil.process_iter(["cmdline"]):
429	        if proc.pid != me and any(folder in arg for arg in proc.info["cmdline"] or () for folder in folders):
430	            found[proc.pid] = proc
431	    for value, procs in processes.marked_processes().items():
432	        if processes.parse_marker(value)[0] in stores:
433	            found.update((p.pid, p) for p in procs)
434	    return list(found.values())
435	
436	
437	def end(procs: list[psutil.Process], *, grace: float = 30.0, rescan: Callable | None = None) -> dict:
438	    """SIGCONT first, since a stopped process cannot act on SIGTERM; then processes.terminate:
439	    SIGTERM, SIGKILL to what is left after grace, and rescans."""
440	    for p in procs:
441	        try:
442	            p.send_signal(signal.SIGCONT)
443	        except psutil.Error:
444	            pass
445	    return processes.terminate(procs, term_grace=grace, kill_confirm=5.0, rescan=rescan)
446	
447	
448	# The machine, and the check
449	
450	def docker_compose(*args: str, timeout: float = 300) -> None:
451	    subprocess.run(["docker", "compose", "-f", str(services.COMPOSE_FILE), *args], check=True,
452	                   capture_output=True, text=True, timeout=timeout)
453	
454	
455	def wait_ready(env: dict) -> None:
456	    subprocess.run([sys.executable, "-m", "etf_risk.services", "ready", *services.SERVICES], cwd=REPO, env=env,
457	                   check=True, timeout=300)
458	
459	
460	def project_containers() -> int:
461	    """This project's containers, running or not, from any worktree: the Compose name is shared."""
462	    out = subprocess.run(["docker", "compose", "-f", str(services.COMPOSE_FILE), "ps", "-aq"],
463	                         capture_output=True, text=True, timeout=60)
464	    if out.returncode != 0:
465	        raise RuntimeError(f"docker compose ps failed with exit code {out.returncode}")
466	    return len(out.stdout.split())
467	
468	
469	def git_dirty() -> bool:
470	    return bool(subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True,
471	                               check=True).stdout.strip())
472	
473	
474	def port_in_use(port: int) -> bool:
475	    with socket.socket() as s:
476	        s.settimeout(1)
477	        return s.connect_ex(("127.0.0.1", port)) == 0
478	
479	
480	def keep_awake() -> None:
481	    """No idle sleep while this process runs; caffeinate ends with it."""
482	    try:
483	        subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])
484	    except OSError:
485	        pass
486	
487	
488	def first_line(*command: str) -> str | None:
489	    try:
490	        out = subprocess.run(command, capture_output=True, text=True, timeout=30)
491	    except (OSError, subprocess.TimeoutExpired):
492	        return None
493	    lines = (out.stdout or out.stderr).strip().splitlines()
494	    return lines[0] if lines else None
495	
496	
497	def tools() -> dict:
498	    vm_memory = first_line("docker", "info", "--format", "{{.MemTotal}}")
499	    return {"uv": first_line("uv", "--version"), "java": first_line("java", "-version"),
500	            "docker": first_line("docker", "version", "--format", "{{.Client.Version}} (server {{.Server.Version}})"),
501	            "compose": first_line("docker", "compose", "version", "--short"),
502	            "python": platform.python_version(), "macos": platform.mac_ver()[0], "cpus": psutil.cpu_count(),
503	            "memory_bytes": psutil.virtual_memory().total,
504	            "docker_vm_memory_bytes": int(vm_memory) if vm_memory and vm_memory.isdigit() else None}
505	
506	
507	@dataclass
508	class System:
509	    """Everything the check does outside this process, so that tests can stand in for each part."""
510	    compose: Callable[..., None]
511	    ready: Callable[[dict], None]
512	    sleep: Callable[[float], None]
513	    host_memory: Callable[[], dict]
514	    available: Callable[[], int]
515	    sampler: Callable[[Path], Sampler]
516	    run_pytest: Callable[..., dict]
517	    leftovers: Callable[[Path], list]
518	    end: Callable[..., dict]
519	    project_containers: Callable[[], int]
520	    other_containers: Callable[[], int]
521	    git_dirty: Callable[[], bool]
522	    port_in_use: Callable[[int], bool]
523	    snapshot_exists: Callable[[], bool]
524	    keep_awake: Callable[[], None]
525	    tools: Callable[[], dict]
526	    code_state: Callable[[], dict]
527	
528	
529	def this_machine() -> System:
530	    return System(compose=docker_compose, ready=wait_ready, sleep=time.sleep, host_memory=host_memory,
531	                  available=available_memory, sampler=Sampler, run_pytest=run_pytest, leftovers=leftovers, end=end,
532	                  project_containers=project_containers, other_containers=services.other_containers,
533	                  git_dirty=git_dirty, port_in_use=port_in_use, snapshot_exists=SNAPSHOT.is_dir,
534	                  keep_awake=keep_awake, tools=tools, code_state=code_state)
535	
536	
537	def preflight(system: System) -> list[str]:
538	    """What keeps the check from starting; empty when nothing does."""
539	    problems = []
540	    try:
541	        if system.git_dirty():
542	            problems.append("the worktree has uncommitted changes")
543	    except (OSError, subprocess.CalledProcessError) as error:
544	        problems.append(f"git: {error}")
545	    try:
546	        if others := system.other_containers():
547	            problems.append(f"{others} running container(s) outside the {services.PROJECT} project")
548	        if ours := system.project_containers():
549	            problems.append(f"{ours} container(s) of the {services.PROJECT} project exist, maybe another session's")
```

## 9. Assistant — 2026-10-24T09:52:56.830Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/worker-pipeline/tests/memory_check.py",
  "offset": 550,
  "limit": 245
}
```

## 10. User — 2026-10-24T09:52:57.123Z

### Tool result

```
550	    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
551	        problems.append(f"docker: {error}")
552	    if busy := [str(port) for port in PORTS if system.port_in_use(port)]:
553	        problems.append(f"port(s) in use: {', '.join(busy)}")
554	    if not system.snapshot_exists():
555	        problems.append(f"no snapshot at {SNAPSHOT.relative_to(REPO)}")
556	    return problems
557	
558	
559	def measure(sampler: Sampler, idle: dict, temp: Path, runs: dict, left: dict) -> dict:
560	    grew = {}
561	    for key in ("compressor", "swap"):
562	        values = [line[f"{key}_bytes"] for line in sampler.host if f"{key}_bytes" in line]
563	        grew[key] = max(values, default=idle[f"{key}_bytes"]) - idle[f"{key}_bytes"]
564	    return {"pytest": runs, "leftovers": left,
565	            "host": {"idle": idle, "available_min_bytes": sampler.available_min,
566	                     "compressor_growth_bytes": grew["compressor"], "swap_growth_bytes": grew["swap"],
567	                     "vm_rss_bytes": sampler.rss["vm"]},
568	            "containers": {service: summarize_container(sampler.readings[service], BUDGETS[service])
569	                           for service in services.SERVICES},
570	            "steps": launcher_peaks(temp / "acceptance"), "jobs": job_peaks(temp / "acceptance"),
571	            "processes": {name: {"rss_bytes": sampler.rss[name], "processes": len(sampler.pids[name])}
572	                          for name in (*ROLES, "pytest")},
573	            "sampler_errors": sampler.errors}
574	
575	
576	def judge(measured: dict) -> dict:
577	    """invalid: why the run does not count. misses: failed runs, leftovers and the container
578	    limits, which alone decide a run that counts. Reported apart, and never deciding: the
579	    supplementary container figures, and the native-process targets, which are not approved."""
580	    invalid: list[str] = []
581	    misses: list[str] = []
582	    for key in ("compressor", "swap"):
583	        grew, limit = measured["host"][f"{key}_growth_bytes"], CONDITIONS[f"{key}_growth"]
584	        if grew > limit:
585	            invalid.append(f"the {key} grew by {size(grew)}, more than {size(limit)}")
586	    for name, run in measured["pytest"].items():
587	        if not run["readable"] or not run["tests"]:
588	            invalid.append(f"pytest {name}: no results")
589	    acceptance = measured["pytest"]["acceptance"]
590	    if acceptance["skipped"]:
591	        invalid.append(f"acceptance cases: {acceptance['skipped']} of {acceptance['tests']} skipped")
592	    for service, c in measured["containers"].items():
593	        if not c["segments"]:
594	            invalid.append(f"{service}: no cgroup reading")
595	        elif any(s["limit_bytes"] != c["budget_bytes"] for s in c["segments"]):
596	            invalid.append(f"{service}: its limit is not its {size(c['budget_bytes'])} budget")
597	    for key in PROPOSED:
598	        if key.startswith("step ") and key.removeprefix("step ") not in measured["steps"]:
599	            invalid.append(f"no launch of {key.removeprefix('step ')} was recorded")
600	    for name in ("worker", "reconciler"):
601	        if not measured["processes"][name]["processes"]:
602	            invalid.append(f"no {name} process was sampled")
603	
604	    for name, run in measured["pytest"].items():
605	        if run["exit_code"] != 0 or run["failures"] or run["errors"]:
606	            misses.append(f"pytest {name}: exit {run['exit_code']}, {run['failures']} failed, {run['errors']} errors")
607	        if measured["leftovers"].get(name):
608	            misses.append(f"pytest {name} left {measured['leftovers'][name]} process(es) behind")
609	    limits = []
610	    for service, c in measured["containers"].items():
611	        over = [(i, s["peak_bytes"]) for i, s in enumerate(c["segments"], 1) if s["peak_bytes"] > c["budget_bytes"]]
612	        for i, peak in over:
613	            misses.append(f"{service} segment {i}: memory.peak {size(peak)}, above its {size(c['budget_bytes'])} limit")
614	        events = {event: c["events"][event] for event in ("oom", "oom_kill")}
615	        for event, count in events.items():
616	            if count:
617	                misses.append(f"{service}: {count} {event} event(s) during the run")
618	        limits.append({"container": service, "limit_bytes": c["budget_bytes"], "peak_bytes": c["peak_bytes"],
619	                       "segment_peaks_bytes": [s["peak_bytes"] for s in c["segments"]], **events,
620	                       "held": bool(c["segments"]) and not over and not any(events.values())})
621	
622	    def against(criterion: str, value: int | None) -> dict:
623	        threshold = PROPOSED.get(criterion)
624	        return {"criterion": criterion, "value": value, "threshold": threshold,
625	                "within": None if threshold is None or value is None else value <= threshold}
626	
627	    container_figures = [against(f"{service} {kind}", value) for service, c in measured["containers"].items()
628	                         for kind, value in (("anon", c["anon_bytes"]), ("limit hits", c["events"]["max"]))]
629	    native = [against(f"step {step}", peak) for step, peak in sorted(measured["steps"].items())]
630	    native += [against(f"process {name}", measured["processes"][name]["rss_bytes"]
631	                       if measured["processes"][name]["processes"] else None) for name in ROLES]
632	    return {"counts": not invalid, "passed": not invalid and not misses, "invalid": invalid, "misses": misses,
633	            "container_limits": limits, "supplementary_container": container_figures,
634	            "native_targets": {"approved": False, "results": native}}
635	
636	
637	def not_counted(reason: str) -> dict:
638	    return {"counts": False, "passed": False, "invalid": [reason], "misses": [], "container_limits": [],
639	            "supplementary_container": [], "native_targets": {"approved": False, "results": []}}
640	
641	
642	def end_leftovers(system: System, temp: Path, record: dict, after: str) -> int:
643	    """End what the runs left behind, record it under ended[after], and say how many there were."""
644	    found = system.leftovers(temp)
645	    if found:
646	        record.setdefault("ended", {})[after] = system.end(found, rescan=lambda: system.leftovers(temp))
647	    return len(found)
648	
649	
650	def run_check(out: Path, temp: Path, keep: bool, system: System) -> int:
651	    record: dict = {"format": 1, "started_at_utc": now(), "code": system.code_state(), "tools": system.tools(),
652	                    "budgets": BUDGETS, "conditions": CONDITIONS,
653	                    "supplementary": {"container": {k: v for k, v in PROPOSED.items() if not k.startswith(NATIVE)},
654	                                      "native": {k: v for k, v in PROPOSED.items() if k.startswith(NATIVE)},
655	                                      "native_approved": False},
656	                    "settle_s": SETTLE_S, "pytest_temp": str(temp), "cleanup_errors": []}
657	    env = {**os.environ, "ETF_RISK_MYSQL_URL": services.DEFAULT_MYSQL_URL,
658	           "ETF_RISK_KAFKA_BOOTSTRAP": services.DEFAULT_KAFKA_BOOTSTRAP}
659	    errors = record["cleanup_errors"]
660	    system.keep_awake()
661	    try:
662	        # the preflight found none of this project's containers, so down -v follows whatever happens
663	        system.compose("up", "-d", "--wait", *services.SERVICES)
664	        system.ready(env)
665	        system.sleep(SETTLE_S)
666	        record["idle"] = idle = system.host_memory()
667	        if idle["available_bytes"] < CONDITIONS["idle_available"]:
668	            record["verdict"] = not_counted(f"{size(idle['available_bytes'])} available with the stack idle, below "
669	                                            f"{CONDITIONS['idle_available'] / GiB:.1f} GiB")
670	            print(f"not ready: {record['verdict']['invalid'][0]}")
671	            return 2
672	        sampler, runs, left = system.sampler(out / "samples.jsonl"), {}, {}
673	        sampler.start()
674	        try:
675	            for name, files, extra in RUNS:
676	                runs[name] = system.run_pytest(name, files, {**env, **extra}, out, temp, TIMEOUTS[name])
677	                print(f"{name}: {runs[name]}")
678	                left[name] = end_leftovers(system, temp, record, name)
679	        finally:
680	            sampler.stop()
681	        record["measured"] = measure(sampler, idle, temp, runs, left)
682	        record["verdict"] = judge(record["measured"])
683	    finally:
684	        try:
685	            end_leftovers(system, temp, record, "cleanup")
686	        except Exception as error:
687	            errors.append(f"ending leftover processes: {error}")
688	        try:
689	            system.compose("down", "-v")
690	        except Exception as error:
691	            errors.append(f"docker compose down -v: {error}")
692	        record["ended_at_utc"] = now()
693	        try:
694	            record["project_containers_after"] = system.project_containers()
695	        except Exception as error:
696	            record["project_containers_after"] = None
697	            errors.append(f"docker compose ps: {error}")
698	        try:
699	            keep_records(temp, out / "records")
700	        except OSError as error:
701	            errors.append(f"copying the records: {error}")
702	        if not keep:
703	            shutil.rmtree(temp, ignore_errors=True)
704	        (out / "record.json").write_text(json.dumps(record, indent=2) + "\n")
705	        for error in errors:
706	            print(f"cleanup: {error}", file=sys.stderr)
707	    report(record)
708	    if errors or record["project_containers_after"]:
709	        print("does not count: the cleanup did not finish; see `docker compose -f docker/compose.yaml ps -a`")
710	        return 2
711	    return 0 if record["verdict"]["passed"] else 1 if record["verdict"]["counts"] else 2
712	
713	
714	def show(criterion: str, value: int | None) -> str:
715	    return "-" if value is None else str(value) if criterion.endswith("limit hits") else size(value)
716	
717	
718	def state(result: dict) -> str:
719	    if result["threshold"] is None:
720	        return "no threshold"
721	    return "not measured" if result["value"] is None else "within" if result["within"] else "above"
722	
723	
724	def conclusion(verdict: dict) -> str:
725	    if not verdict["counts"]:
726	        return "does not count"
727	    if not verdict["passed"]:
728	        return f"failed: {len(verdict['misses'])} miss(es), listed above"
729	    return ("passed: the container limits held, with no oom or oom_kill event, and both pytest runs passed with "
730	            "nothing left behind. This validates the container limits only: the native-process targets are not "
731	            "approved budgets, and this run does not validate them.")
732	
733	
734	def report(record: dict) -> None:
735	    m, verdict = record["measured"], record["verdict"]
736	    print("Container limits, the existing budgets (judged):")
737	    for limit in verdict["container_limits"]:
738	        c = m["containers"][limit["container"]]
739	        print(f"  {limit['container']}: limit {size(limit['limit_bytes'])}; memory.peak {size(limit['peak_bytes'])} "
740	              f"at most, over {len(c['segments'])} segment(s); oom {limit['oom']}, oom_kill {limit['oom_kill']}: "
741	              + ("held" if limit["held"] else "not held"))
742	        for i, s in enumerate(c["segments"], 1):
743	            print(f"    segment {i} ({s['readings']} readings from {s['from_utc']}): memory.peak "
744	                  f"{size(s['peak_bytes'])} of {size(s['limit_bytes'])}; anon {size(s['anon_bytes'])}, file "
745	                  f"{size(s['file_bytes'])}, kernel {size(s['kernel_bytes'])}; events "
746	                  + ", ".join(f"{name} +{count}" for name, count in s["events"].items()))
747	    print("Supplementary container figures (proposed thresholds, reported only):")
748	    for r in verdict["supplementary_container"]:
749	        print(f"  {r['criterion']}: {show(r['criterion'], r['value'])} against "
750	              f"{show(r['criterion'], r['threshold'])}: {state(r)}")
751	    print("Native-process targets (proposed, not approved budgets; reported only, and not validated by this run):")
752	    for r in verdict["native_targets"]["results"]:
753	        sampled = (f" ({m['processes'][r['criterion'].removeprefix('process ')]['processes']} process(es) sampled)"
754	                   if r["criterion"].startswith("process ") else "")
755	        print(f"  {r['criterion']}: {show(r['criterion'], r['value'])} against "
756	              f"{show(r['criterion'], r['threshold'])}: {state(r)}{sampled}")
757	    for job, steps in sorted(m["jobs"].items()):
758	        print(f"    {job}: " + ", ".join(f"{step} {size(peak)}" for step, peak in steps.items()))
759	    h = m["host"]
760	    print(f"Host and harness (recorded only): {size(h['idle']['available_bytes'])} available idle, "
761	          f"{size(h['available_min_bytes'])} at the lowest; compressor {h['compressor_growth_bytes'] / MiB:+,.0f} MiB, "
762	          f"swap {h['swap_growth_bytes'] / MiB:+,.0f} MiB; VM process RSS {size(h['vm_rss_bytes'])}; pytest "
763	          f"{size(m['processes']['pytest']['rss_bytes'])}; {m['sampler_errors']} sampler errors")
764	    for reason in verdict["invalid"]:
765	        print(f"does not count: {reason}")
766	    for miss in verdict["misses"]:
767	        print(f"miss: {miss}")
768	    print(conclusion(verdict))
769	
770	
771	def main(argv: list[str] | None = None, system: System | None = None) -> int:
772	    system = system or this_machine()
773	    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
774	    parser.add_argument("--out", type=Path, help="a new folder for record.json, the samples and the pytest logs")
775	    parser.add_argument("--preflight", action="store_true", help="only check that the run can start")
776	    parser.add_argument("--keep", action="store_true", help="keep pytest's temporary folders with the runs' outputs")
777	    args = parser.parse_args(argv)
778	    if not args.preflight and args.out is None:
779	        parser.error("--out is required, unless --preflight")
780	    problems = preflight(system)
781	    print(f"available now: {size(system.available())}; with the stack up and idle the run needs "
782	          f"{CONDITIONS['idle_available'] / GiB:.1f} GiB")
783	    for problem in problems:
784	        print(f"not ready: {problem}")
785	    if args.preflight or problems:
786	        return 2 if problems else 0
787	    args.out.mkdir(parents=True)   # a new folder, so no record is overwritten
788	    temp = Path(tempfile.mkdtemp(prefix="etf-risk-memory-")).resolve()
789	    return run_check(args.out, temp, args.keep, system)
790	
791	
792	if __name__ == "__main__":
793	    sys.exit(main())
794	
```

## 11. Assistant — 2026-10-24T09:54:02.357Z

I've read the whole tool. Before writing up the pause-related finding, I'm checking how the acceptance harness undoes its own pause and restart injections:

## 12. Assistant — 2026-10-24T09:54:03.050Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/worker-pipeline/tests/test_jobs_live_pipeline.py",
  "offset": 377,
  "limit": 45
}
```

## 13. User — 2026-10-24T09:54:03.340Z

### Tool result

```
377	@pytest.mark.parametrize("stall", ["lock-tables", "pause", "restart"])
378	def test_a_database_stall_during_a_run_needs_no_manual_restart(services, references, stall):
379	    stack = services
380	    stack.worker("A")
381	    job = stack.submit(CALENDAR)
382	    wait_until(lambda: step_running(stack, job, 1), 300, "step 2 of attempt 1")
383	    if stall == "lock-tables":
384	        from etf_risk.jobs import mysql
385	        holder = mysql.connect_mysql(stack.db)
386	        with holder.cursor() as cursor:
387	            cursor.execute("LOCK TABLES jobs WRITE")
388	            time.sleep(8)
389	            cursor.execute("UNLOCK TABLES")
390	        holder.close()
391	    elif stall == "pause":
392	        subprocess.run([*COMPOSE, "pause", "mysql"], check=True, capture_output=True)
393	        time.sleep(8)
394	        subprocess.run([*COMPOSE, "unpause", "mysql"], check=True, capture_output=True)
395	    else:
396	        subprocess.run([*COMPOSE, "restart", "mysql"], check=True, capture_output=True, timeout=120)
397	        subprocess.run([sys.executable, "-m", "etf_risk.services", "ready", "mysql"], check=True,
398	                       capture_output=True, timeout=180, env={**os.environ, "ETF_RISK_MYSQL_URL": MYSQL_URL})
399	    wait_until(lambda: finished(stack, job), 600, f"job {job}")
400	    check(stack, references, job, CALENDAR)
401	    assert stack.procs["A"].poll() is None and stack.procs["reconciler"].poll() is None   # both still serving
402	    renewal_failures = [e for e in stack.events("A") if e["event"] == "renewal_failed"]
403	    print(f"{stall}: {len(renewal_failures)} failed renewals; attempts "
404	          f"{[r['outcome'].value for r in stack.store.attempts(job)]}")
405	
406	
407	def test_a_kafka_restart_during_a_run_needs_no_manual_restart(services, references):
408	    stack = services
409	    stack.worker("A")
410	    job = stack.submit(CALENDAR)
411	    wait_until(lambda: step_running(stack, job, 1), 300, "step 2 of attempt 1")
412	    subprocess.run([*COMPOSE, "restart", "kafka"], check=True, capture_output=True, timeout=120)
413	    wait_until(lambda: finished(stack, job), 600, f"job {job}")
414	    check(stack, references, job, CALENDAR, attempts=1)
415	    second = wait_until(lambda: _submit_when_kafka_is_back(stack), 120, "a submission after the restart")
416	    wait_until(lambda: finished(stack, second), 600, f"job {second}")
417	    check(stack, references, second, CALENDAR)
418	
419	
420	def _submit_when_kafka_is_back(stack):
421	    out = stack.cli("submit", "--snapshot", SNAPSHOT, "--kind", "calendar-year", check=False)
```

## 14. Assistant — 2026-10-24T09:56:40.045Z

Written for: you. The PR checklist at the end is for the PR's reviewers.

I found **9 discrepancies** in [tests/memory_check.py](.claude/worktrees/worker-pipeline/tests/memory_check.py): 3 serious, 2 moderate, 4 minor. None is fixed yet. Nothing was run: no preflight, no test suite, no services. The only extra check was a read-only look showing that the compose file has no named volumes or restart policies, and that this project currently has no Docker volumes or networks.

## Discrepancies

| # | Rule | Where | Problem | Proposed fix |
|---|---|---|---|---|
| 1 | OOM evidence | [run_check](.claude/worktrees/worker-pipeline/tests/memory_check.py#L650) | If the kernel OOM-kills a container's main process, the container stops, and a stopped container can't be read through `docker compose exec`. Compose sets no restart policy. The kill count is then never read: the run fails through pytest, but the container line says "held, oom_kill 0". | After each pytest run and before teardown, read Docker's record of each container's state (`docker inspect`: whether it was OOM-killed, exit code, restart count, start time). An OOM kill or an unexpected stop counts as a container miss. |
| 2 | Event baselines | [memory_check.py:197](.claude/worktrees/worker-pipeline/tests/memory_check.py#L197) | The first segment counts events from its first sample, but its `memory.peak` covers the container's whole life, including startup and the 30 s idle. If that first sample fails, the starting point moves later still, so oom or oom_kill events before it are lost. | Count every segment from zero. The preflight guarantees the containers are fresh, so their counters start at zero. Also record the raw counter values at each segment's first and last sample. **This changes what the OOM rule covers (startup and idle included), so it needs your approval.** |
| 3 | Exit codes | [main:789](.claude/worktrees/worker-pipeline/tests/memory_check.py#L789) | An unhandled error (for example `compose up` failing or the readiness wait timing out) makes Python exit with 1, the same code as "counts, failed". | Catch the error after the record is written, print it, and exit 3. |
| 4 | Leftover detection | [memory_check.py:676-678](.claude/worktrees/worker-pipeline/tests/memory_check.py#L676-L678) | The leftover scan runs the moment pytest exits. Processes still shutting down get counted as left behind and signalled. Examples: a launcher still ending its tree during its 7 s grace after its worker was killed, or PySpark daemons that exit once their JVM's pipe closes. Result: a false failure. | Re-scan for up to 15 s and count only what is still there. |
| 5 | Restart segments | [segments:175-187](.claude/worktrees/worker-pipeline/tests/memory_check.py#L175-L187) | A restart is detected only when `memory.peak` or an event counter goes down. If a new container's first sample already exceeds the old peak and no counter drops, both lives merge into one segment, and that segment's events and figures come out wrong. The overall peak check is unaffected. | Add the container's main-process (PID 1) start time to each sample, read in the same `exec`, and start a new segment when it changes. |
| 6 | Segment completeness | [memory_check.py:679-681](.claude/worktrees/worker-pipeline/tests/memory_check.py#L679-L681) | No sample is taken after the last pytest run, so up to about 5 s at the end is not covered. | Take one final container sample after the sampler stops. |
| 7 | Cleanup | [memory_check.py:689](.claude/worktrees/worker-pipeline/tests/memory_check.py#L689); harness [391-394](.claude/worktrees/worker-pipeline/tests/test_jobs_live_pipeline.py#L391-L394) | The harness unpauses MySQL outside a `finally`, so an interrupted pause case leaves it paused, and cleanup goes straight to `down -v`. Whether that works then depends on how Docker stops a paused container. | Run `docker compose unpause`, ignoring errors, before `down -v`. Optionally also add a `try/finally` in the harness. |
| 8 | Cleanup ownership | [leftovers:421-434](.claude/worktrees/worker-pipeline/tests/memory_check.py#L421-L434) | A process counts as this run's only if its command line names the run's temporary folder or it carries a job-store marker. The JVMs and PySpark daemons of the harness's reference runs have neither. Also, store folders are found only at one fixed depth (`*/*/out/*`). After an interrupted run such processes are neither ended nor counted, though PySpark normally ends them when their JVM exits. | Set an environment variable unique to each pytest run and match on it as well. Find store ids from `job-*-attempt-*` folders at any depth. |
| 9 | Container limits vs native targets | [judge:632](.claude/worktrees/worker-pipeline/tests/memory_check.py#L632) | In `record.json`, the verdict's `"passed"` doesn't say what it covers. The scope appears only in the printed conclusion and in `native_targets.approved: false`. | Add `"validates": "container limits only"` to the verdict. |

**Checked and consistent with the approved rules:**
- **Container limits:** total `memory.peak` is judged per segment against 512 and 640 MiB, and each container's limit must equal its budget.
- **What decides the result:** oom and oom_kill fail a run; anon memory and limit hits are reported only.
- **Native targets:** reported only, marked `approved: false`, and the pass wording says they are not validated.
- **Gates:** fixed at 4.0 GiB and 256 MiB, with no way to relax them. If the idle gate fails, the stack is removed and the tool exits 2.
- **Cleanup scope:**
  - `down -v` runs only after a preflight that found none of this project's containers, so `-v` removes only the unnamed volumes of containers this run created;
  - the only folder deleted is the run's own temporary folder.
- **For your awareness:** a run doesn't count if a step was never launched or no worker or reconciler was sampled, even though those are native figures. That matches the approved "complete results" condition.

**Proposal:** apply all nine fixes in one commit, each with a deterministic test, and run `tests/test_memory_check.py` once. Fix 2 changes a rule, so it needs your yes; the other eight are implementation fixes.

## Machine preparation
1. Stop the other project's 4 containers, for example with `docker compose stop` in its folder; `docker pause` isn't enough. They've been running since 2026-10-23 08:10 UTC. One has restart policy `unless-stopped`, which stays stopped after a manual stop.
2. Restart Docker Desktop, then check that `docker ps` lists nothing.
3. Free memory. Right now: 1.19 GiB available, 3.44 GiB compressed, 12.2 GiB of swap. Restarting the Mac is the reliable way; this session can be resumed afterwards.
4. Keep every other session idle for about 20 minutes, including the recovery-harness session: no tests, Spark, builds or containers.
5. Stay on power, keep the lid open, and leave the machine alone during the run.
6. Tell me when it's ready. I'll run the preflight once, then the check.

## Run command
```bash
cd ~/leveraged-etf-risk-analytics/.claude/worktrees/worker-pipeline
uv run --group jobs python tests/memory_check.py --preflight
uv run --group jobs python tests/memory_check.py --out data/outputs-memory/$(date -u +%Y%m%dT%H%M%SZ)
```
I'd run the second command in the background. It takes about 16 minutes; the time limits are 30 minutes for the job suites and 60 for the acceptance cases.

## What each exit means
| Exit | Meaning | What to do |
|---|---|---|
| 0 | Counts and passed | Record the container results; native figures as reported only; release the window to M3. |
| 1 | Counts and failed | Container limit not held: stop and report; don't rerun for a pass; changing a budget needs your approval. Pytest failure: read `suites.log` or `acceptance.log`; fix in M2 before any rerun. Processes left behind: investigate the harness cleanup first. |
| 2, at preflight | Not ready; nothing started, no folder created | Fix each "not ready:" line. If this project's containers exist, find which session owns them; never remove them automatically. |
| 2, "below 4.0 GiB" | Idle gate failed; stack already removed | Free memory; the threshold stays; rerun into a new folder. |
| 2, "does not count: …" | A run condition failed: compressor or swap grew more than 256 MiB, cases skipped, a container unread, or a step or process never measured | The record is kept but marked invalid. Fix the cause (see `samples.jsonl` and the logs), then rerun into a new folder. |
| 2, "cleanup did not finish" | Containers or processes may remain | Check `docker compose -f docker/compose.yaml ps -a` and the leftover entries in `record.json`. Run `down -v` by hand only after confirming no other session uses the project. |
| 1 with a traceback today (3 after fix 3) | The check crashed | The `record.json` written during cleanup shows how far it got. |
| 130 | Interrupted with Ctrl-C | Cleanup still ran; check as for a cleanup that didn't finish. |

## PR checklist
Written for: reviewers of the M2 PR.

```markdown
### M2 acceptance criteria

Functional, on 6d8a232's code (e4adc38 and a3a767b change documentation only):
- [x] A calendar-year job and a stride-21 job succeed: one accepted attempt each, recorded digest equal to the folder's, all checks and verify pass, tables equal to a direct CLI run
- [x] Worker-only SIGSTOP in step 2: the watchdog ends the tree, no overlapping steps, the old worker is fenced on SIGCONT
- [x] Whole-tree SIGSTOP: the replacement starts no Spark until the frozen tree has ended
- [x] Worker SIGKILL in step 2: nothing survives; the job is recovered
- [x] A step over its time limit is ended and retried until the attempts run out
- [x] Database stalls (LOCK TABLES, pause, restart) and a Kafka restart: no manual restart, one accepted result
- [x] Startup sweep keeps another worker's running attempt
- [x] No leftover processes or Spark/JVM temporary entries; invariant_violations() empty throughout
- [x] Earlier job tests on both stores: offline 551 passed / 29 skipped; live job suites 463 passed / 10 skipped
- [x] Mutation checks: 47/47 offline, 49/49 against MySQL and Kafka

Isolated memory check:
- [x] Memory-check tool and its 74 offline tests (621a409)
- [ ] Review fixes to the tool (2026-10-24 audit), pending approval
- [ ] Container limits held on an isolated machine: total memory.peak within MySQL 512 MiB and Kafka 640 MiB in every restart segment, no oom or oom_kill event, with ≥ 4.0 GiB available idle and compressor and swap growth ≤ 256 MiB each
- [ ] spec §11 ledger: idle available memory with the stack up; per-step peaks for calendar-year and stride 21; the Docker VM process's RSS
- [ ] Offline suite re-run on the final commit for the documented test count
- [ ] Status docs updated with the result

Not part of M2's acceptance: the native-process targets (step trees, worker, reconciler, submit) are proposals, not approved budgets. The check reports figures against them and does not validate them.
```

**Status:** the test window is still mine and unused. Services are stopped, and nothing is pushed or merged (`621a409` is local only). I didn't touch other projects or the M3 worktree. I need two answers from you: whether to apply the fixes (and whether fix 2's rule change is approved), and whether to keep holding the window until the machine is ready or release it to the recovery-harness session now.

`★ Insight ─────────────────────────────────────`
- **Why counting events from zero is consistent:** `memory.peak` counts from the moment a container starts. Event counts should use the same starting point, or startup could produce the peak while an OOM from that same stretch goes uncounted. The preflight guarantees fresh containers, so zero is that starting point.
- **Why exit codes need to be distinct:** anyone who reads only the exit status would see a crash (exit 1 today) as a failed memory budget. Separate codes keep "the measurement said no" apart from "there was no measurement".
`─────────────────────────────────────────────────`
