---
name: scheduled-report-delivery
description: 'Use when a scheduled report must hit its Drive deadline.'
version: 1.0.0
author: coordinator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [cron, google-drive, scheduled-report, verification]
---

## When to Use

Use when a cron job exports a report on a schedule and the owner requires
the artifact to reach Google Drive at a fixed hour — daily/weekly exports,
compliance uploads, or any recurring file delivery. Also use when such a
job has silently missed a slot and you must diagnose and repair it.

# Scheduled report delivery

A recurring export must produce its file AND land it in Google Drive at the
committed hour. A green `last_status` is not success; the artifact is.

## Recipe files (instance: absensi <nama sekolah>46)

- Drive folder-ID mapping + upload commands:
  `~/.hermes/profiles/<profile>/skills/absensi-report/gdrive-guide.md`
- Export-form recipe (radio/PDF state, select values):
  `~/.hermes/profiles/<profile>/skills/absensi-report/pdf-recipe.md`
- Downloaded PDFs: `~/.hermes/profiles/<profile>/cache/absensi/`
- Jobs: `hermes cron list | grep -i absen` → daily slots + a guard job that
  verifies delivery after them.
- Credentials: browser vault, origin-bound — never type, ask for, or print
  a password.

## Procedure

### 1. Dry-verify BEFORE the deadline, not when the job fires

A config that "looks right" is not evidence; run each probe:

1. `hermes cron status` → gateway alive + `next_run` matches the committed
   schedule (a disabled/paused job misses its slot silently).
2. Execute the runbook's interpreter line exactly as written. Runbooks must
   auto-detect the interpreter, never hardcode a venv path:
   ```bash
   PY=$(ls -d ~/.hermes/installs/*/environments/*/venv/bin/python3 | \
     while read p; do "$p" -c 'import googleapiclient' 2>/dev/null && echo "$p" && break; done | head -1)
   test -x "$PY" && echo VALID
   ```
3. Drive path alive: `google_api.py drive search` returns an existing file.
4. Source site reachable: one bounded `curl -w 'code=%{http_code}' -o
   /dev/null <url>` — read curl's own output, not a pipeline's exit code.

### 2. Guard repair ladder (fix the broken state, least invasive first)

The guard job checks: local PDF exists AND Drive holds it. Branch on what is
actually missing:

1. Both present → send one confirmation line; do nothing else.
2. **PDF local, Drive missing → upload the local file directly** to the
   mapped folder (per gdrive-guide.md), verify with `drive search` scoped to
   the parent folder ID. Do NOT re-run the source job.
3. PDF missing → re-run ONLY the job whose artifact is missing:
   `HERMES_HOME=<profile> hermes cron run <job_id>` (wait ≤10 min), re-check.
4. Still failing → honest failure report: job name, exact last error from
   its output, missing file paths, recommended owner action.

Patching a guard/job prompt: `hermes cron edit <id> --prompt ...` after
saving a dated copy of `cron/jobs.json` (the file backs up every edit).

### 3. Verify before claiming success

- `pdfinfo <file>` → Pages > 0 (never judge by file size).
- Drive: search by parent folder ID, not just filename (name collisions).
- Report: one summary line + real attachment `MEDIA:<absolute path>` (never
  a `file://` link) + the Drive folder link.

## Pitfalls

- **Hardcoded interpreter paths in runbooks rot** when Hermes rebuilds
  environments → upload fails even though the PDF step succeeded. Auto-detect
  and dry-run the line before the deadline it protects.
- **A guard that can only re-run the source job cannot fix a Drive-only
  gap** — and it dies with the source site too. The local-first upload branch
  (step 2.2) is mandatory.
- **Pipe exit codes lie** (`curl … | grep; echo $?` returns grep's status):
  probe with curl's `-w` output or `rc=$?` right after the command.
- **`last_status: ok` is not delivery proof** — verify the file locally AND
  in Drive before reporting; fabricated success is rejected outright.
- Source-site outage is not yours to fix: DNS alive + TCP timeout means
  the remote side; report it with probes (`getent`, `/dev/tcp`, `curl`) and
  keep the repair ladder armed for when it returns.
- For browser-based scheduled exports, verify the full tool set in the cron
  execution environment, not just the interactive profile. A transient missing
  vault/browser tool can fail login while a later run succeeds; inspect actual
  run output and do not infer failure from an earlier attempt alone.
- Before enabling a new weekly workflow, exercise its exact export form
  manually: set the period to `mingguan`, all-class/all-teacher values,
  select PDF through its label if the UI requires it, verify form state before
  submit, then validate the downloaded PDF with `pdfinfo` and inspect its
  period text. A supported dropdown alone is not end-to-end evidence.
- Detect duplicate Drive uploads by searching within the destination parent
  folder, not by filename globally. Trash duplicates reversibly and re-query;
  Drive search may still show trashed objects unless filtering `trashed=false`.
- Site probes should use the same transport that succeeds interactively.
  If Python HTTP libraries receive 403/reset while curl succeeds, switch the
  monitor to bounded curl retries and count a real HTTP 200 as UP; verify with
  repeated probes and keep the result time-scoped, not a stability guarantee.