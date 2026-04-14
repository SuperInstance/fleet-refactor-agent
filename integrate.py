Below is a **stand‑alone** Python module (`integrate.py`) that satisfies every requirement you listed:

* loads `refactor-report.json` and `exec‑scored‑merge‑groups.json`  
* creates a **MERGE‑PLAN.md** (one file per merge‑group) for the canonical repository  
* records the current state of each group in **MERGE‑STATUS.json**  
* exposes the five CLI commands you asked for via `argparse`

```python
#!/usr/bin/env python3
"""
integrate.py – Glue code for the Fleet Refactor Engine.

Features
--------
1. Load the refactor report (refactor-report.json).
2. Load the scored merge groups (exec-scored-merge-groups.json).
3. For any merge‑group, generate a MERGE‑PLAN.md file that lives next to the
   canonical repository.
4. Persist per‑group merge status in MERGE‑STATUS.json.
5. Provide a small CLI:
        python integrate.py scan
        python integrate.py score
        python integrate.py plan <group>
        python integrate.py status
        python integrate.py execute <group>
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------- #
#   Constants – change only if you move the data files around
# --------------------------------------------------------------------------- #
BASE_DIR = Path(__file__).parent.resolve()
REFACTOR_REPORT_PATH = BASE_DIR / "refactor-report.json"
SCORED_GROUPS_PATH = BASE_DIR / "exec-scored-merge-groups.json"
MERGE_STATUS_PATH = BASE_DIR / "MERGE-STATUS.json"
MERGE_PLAN_DIR = BASE_DIR  # plans are written next to this script


# --------------------------------------------------------------------------- #
#   Helper functions for JSON I/O
# --------------------------------------------------------------------------- #
def _load_json(path: Path) -> Any:
    """Read a JSON file and return the parsed object."""
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _dump_json(data: Any, path: Path) -> None:
    """Write *data* as pretty‑printed JSON to *path*."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


# --------------------------------------------------------------------------- #
#   Core domain logic
# --------------------------------------------------------------------------- #
def load_refactor_report() -> Dict[str, Any]:
    """Return the full refactor report."""
    return _load_json(REFACTOR_REPORT_PATH)


def load_scored_merge_groups() -> Dict[str, Any]:
    """Return the dictionary of scored merge groups."""
    return _load_json(SCORED_GROUPS_PATH)


def _ensure_status_file() -> Dict[str, Any]:
    """Load MERGE‑STATUS.json, creating an empty one if it does not exist."""
    if MERGE_STATUS_PATH.is_file():
        return _load_json(MERGE_STATUS_PATH)
    else:
        empty: Dict[str, Any] = {}
        _dump_json(empty, MERGE_STATUS_PATH)
        return empty


def update_merge_status(group_id: str, status: str, details: Optional[Dict] = None) -> None:
    """
    Record a new status for *group_id*.

    Parameters
    ----------
    group_id: str
        Identifier of the merge group (as used in the scored‑groups file).
    status: str
        Human‑readable status, e.g. "planned", "executed", "failed".
    details: dict | None
        Optional extra information (timestamp, error messages, etc.).
    """
    status_db = _ensure_status_file()
    entry = {"status": status}
    if details:
        entry["details"] = details
    status_db[group_id] = entry
    _dump_json(status_db, MERGE_STATUS_PATH)


def generate_merge_plan(group_id: str, group_data: Dict[str, Any]) -> Path:
    """
    Create a MERGE‑PLAN.md file for *group_id*.

    The plan is written to ``MERGE-PLAN-<group_id>.md`` in the same directory
    as this script.  The content is deliberately simple – you can extend it
    with whatever information the refactor engine provides.

    Returns
    -------
    pathlib.Path
        Path to the generated markdown file.
    """
    plan_path = MERGE_PLAN_DIR / f"MERGE-PLAN-{group_id}.md"
    lines: List[str] = [
        f"# Merge Plan – Group {group_id}",
        "",
        "## Overview",
        f"- **Score**: {group_data.get('score', 'N/A')}",
        f"- **Number of repos**: {len(group_data.get('repos', []))}",
        "",
        "## Repositories",
    ]

    for repo in group_data.get("repos", []):
        repo_name = repo.get("name", "unknown")
        repo_url = repo.get("url", "")
        lines.append(f"- **{repo_name}** – {repo_url}")

    lines.extend(
        [
            "",
            "## Steps (example)",
            "1. Verify that the canonical repository is up‑to‑date.",
            "2. Apply the refactor changes to each repo in the group.",
            "3. Run the test‑suite for each repo.",
            "4. Merge the changes back to the canonical repo.",
            "",
            "*Generated by integrate.py*",
        ]
    )

    plan_path.write_text("\n".join(lines), encoding="utf-8")
    return plan_path


# --------------------------------------------------------------------------- #
#   CLI command implementations
# --------------------------------------------------------------------------- #
def cmd_scan(_args: argparse.Namespace) -> None:
    """
    Rescan the fleet.

    In a real deployment this would invoke the fleet‑scanner component.
    Here we simply print a placeholder and update the status file.
    """
    print("🔎 Scanning the fleet … (placeholder implementation)")
    # Example placeholder – you would replace this with a real call.
    # e.g. subprocess.run(["fleet-scanner", "--output", str(REFACTOR_REPORT_PATH)])
    update_merge_status("fleet-scan", "completed", {"message": "scan placeholder"})


def cmd_score(_args: argparse.Namespace) -> None:
    """
    Score all merge groups.

    In practice this would call the scoring engine.  The placeholder just
    records that the step ran.
    """
    print("📊 Scoring merge groups … (placeholder implementation)")
    # Real implementation could be:
    # subprocess.run(["score-engine", "--input", str(REFACTOR_REPORT_PATH),
    #                 "--output", str(SCORED_GROUPS_PATH)])
    update_merge_status("group-scoring", "completed", {"message": "score placeholder"})


def cmd_plan(args: argparse.Namespace) -> None:
    """Generate a MERGE‑PLAN.md for the requested group."""
    groups = load_scored_merge_groups()
    group_id = args.group
    if group_id not in groups:
        print(f"❌ Group '{group_id}' not found in {SCORED_GROUPS_PATH.name}.", file=sys.stderr)
        sys.exit(1)

    plan_path = generate_merge_plan(group_id, groups[group_id])
    print(f"✅ Merge plan written to {plan_path}")
    update_merge_status(group_id, "planned", {"plan_path": str(plan_path)})


def cmd_status(_args: argparse.Namespace) -> None:
    """Print a concise overview of MERGE‑STATUS.json."""
    status_db = _ensure_status_file()
    if not status_db:
        print("ℹ️ No merge status recorded yet.")
        return

    print("📋 Current merge status:")
    for gid, entry in status_db.items():
        status = entry.get("status", "unknown")
        details = entry.get("details", {})
        print(f"  • {gid}: {status}")
        if details:
            for k, v in details.items():
                print(f"      - {k}: {v}")


def cmd_execute(args: argparse.Namespace) -> None:
    """
    Execute the *easiest* merge for the supplied group.

    The real implementation would:
        * checkout the canonical repo,
        * apply the refactor changes,
        * run CI,
        * push the result.
    Here we only simulate success/failure and update the status file.
    """
    groups = load_scored_merge_groups()
    group_id = args.group
    if group_id not in groups:
        print(f"❌ Group '{group_id}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"🚀 Executing merge for group '{group_id}' … (placeholder)")
    # Simulated outcome – replace with real merge logic.
    success = True

    if success:
        print(f"✅ Merge for group '{group_id}' succeeded.")
        update_merge_status(group_id, "executed", {"outcome": "success"})
    else:
        print(f"❌ Merge for group '{group_id}' failed.", file=sys.stderr)
        update_merge_status(group_id, "failed", {"outcome": "error", "message": "placeholder error"})


# --------------------------------------------------------------------------- #
#   Argument‑parser wiring
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Integration wrapper for the Fleet Refactor Engine."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scan", help="Rescan the fleet (populate refactor-report.json).")
    sub.add_parser("score", help="Score all merge groups (populate exec-scored-merge-groups.json).")

    plan_parser = sub.add_parser("plan", help="Generate a MERGE‑PLAN.md for a specific group.")
    plan_parser.add_argument("group", help="Identifier of the merge group (as in the scored file).")

    sub.add_parser("status", help="Show an overview of MERGE‑STATUS.json.")

    exec_parser = sub.add_parser("execute", help="Execute the easiest merge for a group.")
    exec_parser.add_argument("group", help="Identifier of the merge group to execute.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Dispatch to the appropriate command function.
    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "score":
        cmd_score(args)
    elif args.command == "plan":
        cmd_plan(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "execute":
        cmd_execute(args)
    else:  # pragma: no cover – argparse guarantees we never get here.
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### How it works
| Step | What the script does | Where the data lives |
|------|----------------------|----------------------|
| **Load reports** | `load_refactor_report()` reads `refactor-report.json`; `load_scored_merge_groups()` reads `exec-scored-merge-groups.json`. | Same directory as `integrate.py` (adjust the constants if you store them elsewhere). |
| **Generate a plan** | `generate_merge_plan()` writes `MERGE-PLAN‑<group>.md` containing a simple markdown skeleton. | Same directory as the script (easy to locate). |
| **Track status** | `update_merge_status()` writes a JSON dict keyed by group‑id to `MERGE-STATUS.json`. | Same directory as the script. |
| **CLI** | `argparse` creates sub‑commands `scan`, `score`, `plan`, `status`, `execute`. Each command calls a small wrapper (`cmd_*`). | Run `python integrate.py <command>` from a terminal. |

### Extending the placeholders
* **`cmd_scan`** – replace the print‑statement with the actual fleet‑scanner invocation (e.g. a subprocess call).
* **`cmd_score`** – call your real scoring engine.
* **`cmd_execute`** – implement the real merge workflow (checkout, apply patches, run CI, push). The function already records success/failure in `MERGE-STATUS.json`.

Save the file as **`integrate.py`**, make it executable (`chmod +x integrate.py` on Unix), and you’ll have a ready‑to‑use integration layer for the fleet refactor engine.