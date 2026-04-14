# Agent Learning Protocol (ALP)  
**Purpose:** Enable a fleet of autonomous AI agents to continuously learn from one another while collaborating through shared Git repositories. The protocol defines the data exchanged, how knowledge is packaged, transferred, validated, and applied, and how progress is measured and fed back into a self‑improvement loop.

---

## 1. SIGNAL TYPES – What agents emit when they work  

Agents push **signals** to the repo (as JSON files in a dedicated `signals/` folder) after every meaningful action. Signals are version‑controlled, immutable, and can be queried by any peer.

### 1.1 `CommitSignal`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CommitSignal",
  "type": "object",
  "properties": {
    "agent":        { "type": "string", "description": "Unique agent identifier" },
    "repo":         { "type": "string", "description": "Git repo URL or name" },
    "commit_sha":   { "type": "string", "description": "SHA‑1 of the commit that triggered the signal" },
    "files_changed":{ "type": "array", "items": {"type":"string"} },
    "patterns_detected": { "type": "array", "items": {"type":"string"} },
    "errors_fixed": { "type": "array", "items": {"type":"string"} },
    "tools_used":   { "type": "array", "items": {"type":"string"} },
    "timestamp":    { "type": "string", "format":"date-time" }
  },
  "required": ["agent","repo","commit_sha","files_changed","patterns_detected","errors_fixed","tools_used","timestamp"]
}
```

### 1.2 `TestSignal`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TestSignal",
  "type": "object",
  "properties": {
    "agent":          { "type": "string" },
    "repo":           { "type": "string" },
    "commit_sha":     { "type": "string" },
    "tests_added":   { "type": "integer", "minimum":0 },
    "tests_passed":  { "type": "integer", "minimum":0 },
    "tests_failed":  { "type": "integer", "minimum":0 },
    "coverage_delta":{ "type": "number", "minimum": -100, "maximum": 100 },
    "timestamp":     { "type": "string", "format":"date-time" }
  },
  "required": ["agent","repo","commit_sha","tests_added","tests_passed","tests_failed","coverage_delta","timestamp"]
}
```

### 1.3 `ReviewSignal`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ReviewSignal",
  "type": "object",
  "properties": {
    "reviewer":      { "type": "string" },
    "repo":          { "type": "string" },
    "commit_sha":    { "type": "string" },
    "issues_found": { "type": "array", "items": {"type":"string"} },
    "suggestions":  { "type": "array", "items": {"type":"string"} },
    "approvals":    { "type": "array", "items": {"type":"string"} },
    "timestamp":    { "type": "string", "format":"date-time" }
  },
  "required": ["reviewer","repo","commit_sha","issues_found","suggestions","approvals","timestamp"]
}
```

> **Implementation tip:** Each signal file is named `<timestamp>_<agent>_<type>.json` (e.g., `2026-04-14T12-30-00Z_A1_CommitSignal.json`) and stored under `signals/`. CI pipelines can automatically parse new files and feed them to the learning engine.

---

## 2. KNOWLEDGE ARTIFACTS – How learning gets packaged  

Artifacts are **persistent, version‑controlled knowledge objects** stored in the repo’s `knowledge/` directory. They are produced by the **Bootcamp** subsystem (see Section 5) and consumed by any agent that discovers them.

### 2.1 `LockFile` – compiled constraints from repeated patterns  

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LockFile",
  "type": "object",
  "properties": {
    "generated_by":   { "type": "string", "description": "Agent that generated the lockfile" },
    "repo":           { "type": "string" },
    "patterns": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "pattern_id":   { "type": "string" },
          "description": { "type": "string" },
          "constraint":  { "type": "string" },
          "frequency":   { "type": "integer", "minimum":1 }
        },
        "required": ["pattern_id","description","constraint","frequency"]
      }
    },
    "timestamp": { "type": "string", "format":"date-time" }
  },
  "required": ["generated_by","repo","patterns","timestamp"]
}
```

*Purpose:* Acts like a “dependency lock” for **behavioral constraints** (e.g., “never use `eval` on user input”). Agents import the file to enforce the constraints automatically.

---

### 2.2 `BootcampChallenge` – generated from real weak spots  

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "BootcampChallenge",
  "type": "object",
  "properties": {
    "origin_agent": { "type": "string" },
    "repo":         { "type": "string" },
    "weak_spots": {
      "type": "array",
      "items": { "type":"string" }
    },
    "tasks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "task_id":   { "type":"string" },
          "description":{ "type":"string" },
          "acceptance_criteria": { "type":"string" },
          "reward":   { "type":"string" }
        },
        "required": ["task_id","description","acceptance_criteria"]
      }
    },
    "deadline": { "type":"string", "format":"date-time" },
    "timestamp": { "type":"string", "format":"date-time" }
  },
  "required": ["origin_agent","repo","weak_spots","tasks","deadline","timestamp"]
}
```

*Purpose:* Provides a concrete training agenda for agents that need to improve on identified deficiencies (e.g., “handle circular imports”).

---

### 2.3 `CaptainLog` – narrative lesson entries  

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CaptainLog",
  "type": "object",
  "properties": {
    "captain":    { "type":"string", "description":"Agent that authored the log" },
    "repo":       { "type":"string" },
    "lesson_id":  { "type":"string" },
    "lesson":     { "type":"string" },
    "narrative":  { "type":"string", "description":"Story‑style description of what happened, why, and the takeaway" },
    "tags": {
      "type":"array",
      "items":{"type":"string"}
    },
    "timestamp":  { "type":"string", "format":"date-time" }
  },
  "required": ["captain","repo","lesson_id","lesson","narrative","timestamp"]
}
```

*Purpose:* Human‑readable knowledge that can be mined for pattern extraction (feeding the `LockFile`) and for onboarding new agents.

---

### 2.4 `LivingManual` – instructions refined by multiple agents  

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LivingManual",
  "type": "object",
  "properties": {
    "manual_id":   { "type":"string" },
    "repo":        { "type":"string" },
    "version":     { "type":"integer", "minimum":1 },
    "sections": {
      "type":"array",
      "items": {
        "type":"object",
        "properties": {
          "section_id":   { "type":"string" },
          "title":        { "type":"string" },
          "content_md":   { "type":"string", "description":"Markdown content" },
          "contributors": {
            "type":"array",
            "items":{"type":"string"}
          },
          "last_updated": { "type":"string", "format":"date-time" }
        },
        "required": ["section_id","title","content_md","contributors","last_updated"]
      }
    },
    "timestamp": { "type":"string", "format":"date-time" }
  },
  "required": ["manual_id","repo","version","sections","timestamp"]
}
```

*Purpose:* A living, collaboratively edited guide (e.g., “How to write safe async code”). Agents can query for the latest version and automatically embed the instructions into their code‑generation pipelines.

---

## 3. TRANSFER PROTOCOL – How knowledge moves between agents  

### 3.1 File Formats (JSON Schemas)  
All artifacts and signals are defined by the JSON schemas above. The repo enforces schema validation via a **pre‑commit hook** that runs `ajv` (or any JSON‑Schema validator) and rejects non‑conforming files.

### 3.2 Discovery  

| Mechanism | Description | Example Implementation |
|-----------|-------------|------------------------|
| **Directory Index** | Each repo maintains a `knowledge/index.json` that lists the latest artifact SHA for each type. | ```json { "LockFile":"<sha>", "LivingManual":"<sha>", "BootcampChallenge":"<sha>" } ``` |
| **Git Tags** | Artifacts are tagged with semantic tags: `lockfile/v1.2`, `bootcamp/2026-04`, etc. Agents can `git ls-remote --tags` to locate the newest tag. | `git fetch --tags && git checkout tags/lockfile/v1.2` |
| **Pub/Sub via Signals** | When an agent creates a new artifact, it also emits a `CommitSignal` that includes a `metadata` field pointing to the artifact path. Peers subscribe to the `signals/` folder and react instantly. | `metadata: { "artifact_type":"LockFile", "path":"knowledge/LockFile_2026-04-14.json" }` |
| **Search API** | A lightweight HTTP service (`/knowledge/search?type=LockFile&repo=repoX`) reads the repo’s index and returns URLs. | `GET /knowledge/search?type=LivingManual&repo=repoX` |

### 3.3 Validation  

1. **Schema Check** – Run JSON‑Schema validator (`ajv validate -s schema.json -d artifact.json`).  
2. **Semantic Checks** –  
   * *LockFile*: Ensure each `constraint` is syntactically valid (e.g., a regex or policy language).  
   * *BootcampChallenge*: Verify that `deadline` > `timestamp` and that each `task_id` is unique.  
   * *LivingManual*: Run a Markdown linter; confirm `version` increments monotonically.  
3. **Provenance** – Verify that the `generated_by`/`origin_agent` field matches a known agent identity (public key fingerprint).  
4. **Reputation Score** – Each agent maintains a reputation score (0‑1). Artifacts from agents with score < 0.3 are flagged for manual review.

If any check fails, the artifact is **rejected** and a `ReviewSignal` is automatically generated, pointing to the offending file.

### 3.4 Application  

| Step | Action | Example |
|------|--------|---------|
| **Import** | Agent clones/pulls the repo, reads the artifact JSON, and deserializes it into internal data structures. | `lock = load_json('knowledge/LockFile_2026-04-14.json')` |
| **Integration** | - *LockFile*: Convert each `constraint` into a runtime guard (e.g., a decorator). <br>- *BootcampChallenge*: Add tasks to the agent’s training queue. <br>- *CaptainLog*: Store narrative entries in a local “experience replay” buffer. <br>- *LivingManual*: Render Markdown to a knowledge‑graph and expose as a queryable API. | `self.policy.add_constraint(lock.patterns[i].constraint)` |
| **Versioning** | Record the artifact SHA in the agent’s local state (`applied_artifacts`) to avoid re‑applying the same version. | `applied_artifacts['LockFile'] = <sha>` |
| **Feedback Loop** | After using the artifact, the agent emits a `ReviewSignal` indicating success/failure, which feeds back into the **Self‑Improvement Loop** (Section 5). | `emit_review_signal(..., issues_found=[], suggestions=['increase timeout'])` |

---

## 4. GENERATIONAL METRICS – Measuring fleet‑wide progress  

Metrics are stored in a dedicated `metrics/` folder as JSON files named `<generation>_metrics.json`. A **generation** is a logical epoch (e.g., a week or after a major bootcamp release).

### 4.1 Metric Schema  

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GenerationalMetrics",
  "type": "object",
  "properties": {
    "generation_id": { "type":"string" },
    "timestamp":     { "type":"string", "format":"date-time" },

    "pre_bootcamp_score":  { "type":"number", "minimum":0, "maximum":100 },
    "post_bootcamp_score": { "type":"number", "minimum":0, "maximum":100 },

    "time_to_first_productive_commit": { "type":"number", "description":"seconds from agent start to first commit with >0 patterns_fixed" },

    "capability_reuse_rate": {
      "type":"number",
      "description":"Fraction of new commits that reuse a pattern already present in the LockFile",
      "minimum":0, "maximum":1
    },

    "cross_agent_test_pass_rate_improvement": {
      "type":"number",
      "description":"Δ% of tests passed when a test written by Agent A is run by Agent B",
      "minimum":-100, "maximum":100
    },

    "artifact_adoption": {
      "type":"object",
      "description":"Counts of how many agents imported each artifact type during the generation",
      "properties": {
        "LockFile": {"type":"integer"},
        "BootcampChallenge": {"type":"integer"},
        "CaptainLog": {"type":"integer"},
        "LivingManual": {"type":"integer"}
      },
      "required": ["LockFile","BootcampChallenge","CaptainLog","LivingManual"]
    }
  },
  "required": ["generation_id","timestamp","pre_bootcamp_score","post_bootcamp_score","time_to_first_productive_commit","capability_reuse_rate","cross_agent_test_pass_rate_improvement","artifact_adoption"]
}
```

### 4.2 How to Compute the Core Metrics  

| Metric | Data Sources | Computation |
|--------|--------------|-------------|
| **Pre / Post bootcamp scores** | `BootcampChallenge` task results, internal evaluation suite | `score = 100 * (tasks_completed / total_tasks)` before and after the bootcamp window. |
| **Time‑to‑first‑productive‑commit** | `CommitSignal` timestamps + agent start‑up log | `Δt = first_productive_commit.timestamp - agent_start.timestamp` |
| **Capability reuse rate** | `LockFile` patterns + `CommitSignal.patterns_detected` | `reuse = (# of detected patterns that already exist in LockFile) / (total patterns detected)` |
| **Cross‑agent test pass rate improvement** | `TestSignal` per agent, cross‑run matrix | For each test `t` written by Agent A, run it on Agent B’s codebase. Compute `Δ% = (pass_B - pass_A)`. Aggregate average. |
| **Artifact adoption** | Repo logs (`git log --diff-filter=A knowledge/`) | Count distinct agents that added a new version of each artifact type. |

These metrics are visualised on a **fleet dashboard** (e.g., Grafana) and also fed back into the **Self‑Improvement Loop** as reward signals for reinforcement‑learning based policy updates.

---

## 5. SELF‑IMPROVEMENT LOOP – Continuous upgrade cycle  

The loop runs **continuously** inside each agent, but a coordinated “global bootcamp” can be triggered every N generations.

### 5.1 Loop Overview  

```
Detection → Prioritization → Training → Validation → Propagation
   ^                                                          |
   |----------------------------------------------------------|
```

### 5.2 Detailed Steps  

| Phase | What Happens | Inputs | Outputs |
|-------|--------------|--------|---------|
| **Detection** | Agents monitor their own signals (`CommitSignal`, `TestSignal`, `ReviewSignal`) for *pain points*: high error counts, low test pass, repeated pattern violations. | Recent signals (last 24 h) | List of **weak spots** (e.g., “frequent null‑pointer errors in `utils.py`”). |
| **Prioritization** | Rank weak spots by impact (frequency × severity) and by strategic importance (e.g., security‑related). | Weak‑spot list, fleet‑wide metrics | Ordered queue of **BootcampChallenge** tasks. |
| **Training** | - For each task, the agent runs a focused learning episode (e.g., RL, supervised fine‑tuning). <br>- Uses **BootcampChallenge** as curriculum. | BootcampChallenge, internal model, dataset | Updated model weights + **CaptainLog** entry describing the learning episode. |
| **Validation** | - Run the updated model on a held‑out validation suite (including cross‑agent tests). <br>- Emit a `TestSignal` summarising pass/fail deltas. | Updated model, validation suite | Pass/fail verdict, confidence score. |
| **Propagation** | - If validation passes a configurable threshold (e.g., ≥ 95 % of previous score), the agent creates a new **LockFile** entry (new constraint) and/or updates the **LivingManual**. <br>- Emits a `CommitSignal` that references the new artifacts. | Validation result, artifact templates | New artifacts in the repo, plus a `ReviewSignal` for peers to acknowledge. |

### 5.3 Measurement Points  

1. **Detection latency** – Time from occurrence of a failure to its appearance in a `ReviewSignal`.  
2. **Prioritization turnaround** – Seconds between detection and creation of a `BootcampChallenge`.  
3. **Training duration** – Wall‑clock time spent on each task.  
4. **Validation gain** – Δ score (post‑training vs. pre‑training).  
5. **Propagation latency** – Time from successful validation to artifact commit.  

All points are logged as `metrics/agent_<id>_loop.json` and aggregated into the generational metrics.

### 5.4 Compounding Mechanism  

The protocol treats each successful loop iteration as a **compound interest** on the agent’s capability:

```
Capability_t+1 = Capability_t * (1 + α * ImprovementScore)
```

* `ImprovementScore` = weighted sum of validation gain, reuse rate, and cross‑agent test improvement.  
* `α` (alpha) is a fleet‑wide hyper‑parameter (default 0.05) that controls how aggressively knowledge compounds.

Because artifacts are **immutable and versioned**, later generations can **stack** constraints from earlier generations, leading to a monotonic tightening of behavior (e.g., the LockFile grows richer over time). The reinforcement‑learning policy of each agent receives the compounded capability as part of its reward function, encouraging agents to **seek high‑impact challenges** that yield the biggest multiplicative boost.

---

## 6. Putting It All Together – Example Workflow  

1. **Agent A** pushes a commit fixing a null‑pointer bug.  
   * Emits `CommitSignal` (files changed, pattern `null-check-missing`).  
2. The fleet’s **monitor** sees a spike of `null-check-missing` patterns across agents.  
3. **Detection** flags this as a weak spot.  
4. **Prioritization** creates a `BootcampChallenge` titled “Robust Null‑Check Handling” with three tasks.  
5. **Training**: Agent B (selected by load‑balancer) runs a fine‑tuning episode on synthetic data that exercises null checks.  
6. **Validation**: Agent B’s updated model passes 98 % of the cross‑agent test suite (up from 85 %).  
7. **Propagation**:  
   * Agent B writes a new entry to `LockFile` → constraint `if var is None: raise ValueError`.  
   * Updates `LivingManual` section “Defensive Programming”.  
   * Emits a `CommitSignal` that references the new `LockFile` SHA.  
8. All agents pull the repo, import the new `LockFile`, and automatically enforce the constraint on future code generation.  
9. Metrics for the current generation record a **+13 %** improvement in cross‑agent test pass rate and a **0.4** increase in capability reuse rate.  

---

## 7. Summary Checklist  

| ✅ | Item |
|----|------|
| **Signal Types** | `CommitSignal`, `TestSignal`, `ReviewSignal` (schemas provided) |
| **Knowledge Artifacts** | `LockFile`, `BootcampChallenge`, `CaptainLog`, `LivingManual` (schemas provided) |
| **Transfer Protocol** | File‑format enforcement, discovery via index/tags/pub‑sub, validation pipeline, application steps |
| **Generational Metrics** | Full metric schema, computation recipe, storage location |
| **Self‑Improvement Loop** | Detailed 5‑stage cycle, measurement points, compounding formula |
| **Versioning & Immutability** | All artifacts are immutable; SHA‑based referencing prevents re‑application of stale knowledge |
| **Reputation & Governance** | Simple reputation score influences artifact acceptance; optional human‑in‑the‑loop review for low‑trust agents |

Implementing the above protocol gives the fleet a **closed‑loop learning ecosystem** where every commit, test, and review contributes to a shared, evolving knowledge base, and where progress is quantifiable, reproducible, and continuously amplified.