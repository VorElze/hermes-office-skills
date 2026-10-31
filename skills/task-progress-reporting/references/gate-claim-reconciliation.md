# Gate claim reconciliation

Use when a gate/audit card reports a verdict (APPROVE / REVISE / LULUS) backed
by aggregate counts. The worker's narrative is a claim; the arithmetic is the
proof. A gate can pass on real work and still quote a number its own artifacts
do not produce — that is exactly what a coordinator is for.

## Where the artifacts actually are

1. Worker scratch, not the repo:
   `~/.hermes/profiles/<worker>/cache/scratch/<task-slug>/`
   `ls -l --time-style='+%H:%M:%S'` there shows every probe round and its size.
2. `docs/evidence/...` in the repo usually holds only the narrative verdict.
3. `/tmp/<slug>/` may hold an EARLIER round (smaller row counts, older mtime).
   Never reconcile against it unless its file timestamps match the verdict time.
4. Identify the summariser first — e.g. `gate-metrics.json`: it lists the
   intended denominators (node counts per probe, min ratios, flag booleans).

## Procedure

1. Read the verdict's quoted numbers into a list: total instances, min value per
   metric, failure count, excluded-row counts.
2. List each raw result file with row count and mtime; map each to a probe.
3. Recompute in Python (no grep eyeballing):

   ```python
   import json
   def tot(rows, skip=None):
       n = f = 0
       for r in rows:
           if skip and str(r.get('cfg')) == skip:
               continue
           n += r.get('checked', 0)
           f += len(r.get('fails', []))
       return n, f
   ```

4. Reconcile the sum: `walker + vp(minus excluded) + base = quoted total`.
   Add each component AFTER its exclusions are already removed — subtracting the
   excluded rows a second time manufactures a mismatch that is not there. A
   mismatch of exactly the excluded-row count means the report forgot to say
   which rows were dropped; any other mismatch means the headline is wrong.
5. Check every minimum against its threshold (contrast `>=4.5`, clearance px,
   touch target `>=44px`, overflow `==0`) — recompute from rows, not from the
   summary file.
6. Classify suspicious booleans: open the rows the flag summarises. A key the
   summariser never populated (`borderline_pass`, `c390_*`) is a script artifact;
   a populated key below threshold is a real failure. Report the class, not the
   raw flag.
7. State the arithmetic in every report quoting the verdict. `"28.938
diperiksa, 0 gagal"` alone is not auditable; `"12.025 walker + 12.064 VP
(464 baris inventaris sudah dikeluarkan dari probe itu) + 4.849 base = 28.938,
0 gagal"` is. Every expression you write must add up as written — an example
whose terms do not sum to the headline teaches the next reader to subtract
exclusions twice.

## What each evidence class actually proves

| Evidence | Proves | Does NOT prove |
|---|---|---|
| file size, mtime | worker wrote something | correctness |
| `git diff --stat` | scope edited | that gates ran |
| tool-call histogram from `state.db` | continuous work | output quality |
| message buckets per 10 min | no silent stretch | progress toward acceptance |
| raw JSON reconciliation | the quoted verdict numbers | that unmeasured criteria pass |

## What a coordinator recomputation does and does not settle

Re-deriving the headline from raw rows proves the NUMBERS. It does not close
the gate card: the gate still needs a written verdict in the evidence file
from the gate profile, and the card still needs to be closed. Do not promote
the downstream card on your own recomputation, and do not re-run the same gate
over unchanged evidence to manufacture that verdict — it blocks again and
burns the card's budget.

## On mismatch

Do not accept the verdict and do not silently "fix" the number yourself. Post
one comment naming the discrepancy and the one artifact that would settle it
(a single file whose row sum equals the quoted total), cap the card's remaining
minutes, and require the restated denominator in the final verdict. If the
round is out of budget, accept the RECOMPUTED figure as the gate result — the
underlying rows are the evidence, not the summary line.
