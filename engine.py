#!/usr/bin/env python3
"""
Fleet Refactor Engine - The Shipwright's Tools
Scans SuperInstance fleet for duplicates, overlap, merge candidates.
"""
import json, os, sys, urllib.request, ssl, time, hashlib, re
from collections import defaultdict
from datetime import datetime

GH = os.environ.get("GITHUB_TOKEN", "")
ctx = ssl.create_default_context()

def api(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {GH}"})
    return json.loads(urllib.request.urlopen(req, timeout=15, context=ctx).read())

def get_all_repos(org, per_page=100):
    repos = []
    page = 1
    while True:
        data = api(f"https://api.github.com/orgs/{org}/repos?per_page={per_page}&page={page}&sort=updated")
        if not data:
            break
        repos.extend(data)
        page += 1
        if len(data) < per_page:
            break
    return repos

def get_tree(repo_full_name):
    for branch in ["main", "master"]:
        try:
            data = api(f"https://api.github.com/repos/{repo_full_name}/git/trees/{branch}?recursive=1")
            return [t["path"] for t in data.get("tree", []) if t["type"] == "blob"]
        except:
            continue
    return []

def extract_languages(files):
    ext_map = {
        ".py": "Python", ".rs": "Rust", ".go": "Go", ".c": "C", ".h": "C",
        ".js": "JavaScript", ".ts": "TypeScript", ".zig": "Zig", ".cu": "CUDA",
        ".java": "Java", ".json": "JSON", ".toml": "TOML", ".yml": "YAML",
    }
    return sorted(set(ext_map[os.path.splitext(f)[1]] for f in files if os.path.splitext(f)[1] in ext_map))

def compute_signature(files):
    key_patterns = [
        "vm", "runtime", "interpreter", "assembler", "compiler", "opcode", "isa",
        "test", "mud", "holodeck", "agent", "fleet", "keeper", "monitor",
        "mechanic", "bootcamp", "skill", "flux", "signalk", "cocapn", "priority",
        "camera", "anomaly", "twin", "capdb", "baton", "bottle", "i2i",
        "envelope", "a2a", "deckboss", "commodore", "dockside", "greenhorn",
    ]
    sig = []
    for f in files:
        fl = f.lower()
        for p in key_patterns:
            if p in fl:
                sig.append(p)
    return sorted(set(sig))

def categorize_repo(repo_data, files, signature):
    name = repo_data["name"].lower()
    desc = (repo_data.get("description") or "").lower()
    all_text = name + " " + desc + " " + " ".join(signature)

    categories = {
        "flux-runtime": ["flux", "vm", "runtime", "interpreter", "bytecode", "opcode", "isa", "assembler"],
        "holodeck": ["holodeck", "mud", "room", "studio"],
        "fleet-infra": ["fleet", "agent-api", "keeper", "monitor", "mechanic", "dashboard"],
        "agent-std": ["git-agent", "standard", "dockside", "bootcamp", "charter"],
        "cocapn": ["cocapn", "signalk", "boat", "marine", "vessel", "captain", "deckboss"],
        "flux-skills": ["skill", "murmur", "spreader", "dream", "streamer"],
        "research": ["research", "experiment", "paper", "lock", "dcs", "abstraction"],
        "i2i": ["i2i", "iron", "bottle", "envelope", "protocol", "baton", "mesosynchronous"],
        "brand": ["brand", "logo", "image", "cultural", "fleet-english", "fleet-chinese"],
        "testing": ["test", "conformance", "coverage", "benchmark"],
    }

    matches = {}
    for cat, keywords in categories.items():
        score = sum(1 for k in keywords if k in all_text)
        if score > 0:
            matches[cat] = score

    if matches:
        return max(matches, key=matches.get)
    return "uncategorized"


class FleetRefactorEngine:
    def __init__(self):
        self.repos = {}
        self.categories = defaultdict(list)
        self.duplicates = []
        self.merge_candidates = []

    def scan(self):
        print("Scanning SuperInstance fleet...")
        repos = get_all_repos("SuperInstance")
        print("Found %d repos" % len(repos))

        for r in repos:
            if r.get("fork"):
                continue
            name = r["name"]
            files = get_tree(r["full_name"])
            sig = compute_signature(files)
            langs = extract_languages(files)
            category = categorize_repo(r, files, sig)

            self.repos[name] = {
                "full_name": r["full_name"],
                "description": r.get("description"),
                "language": r.get("language"),
                "languages": langs,
                "files_count": len(files),
                "signature": sig,
                "category": category,
                "pushed_at": r.get("pushed_at"),
                "stars": r.get("stargazers_count", 0),
                "has_tests": any("test" in f.lower() for f in files),
                "has_ci": any(f.startswith(".github/workflows") for f in files),
                "has_charter": "CHARTER.md" in files,
                "has_readme": "README.md" in files,
                "files": files[:50],
            }
            self.categories[category].append(name)
            time.sleep(0.25)

        print("Categorized %d non-fork repos" % len(self.repos))
        for cat, names in sorted(self.categories.items()):
            print("  %s: %d repos" % (cat, len(names)))

    def find_duplicates(self):
        print("\nFinding duplicates...")

        for cat, repo_names in self.categories.items():
            if len(repo_names) < 2:
                continue
            for i, name_a in enumerate(repo_names):
                for name_b in repo_names[i + 1:]:
                    sig_a = set(self.repos[name_a]["signature"])
                    sig_b = set(self.repos[name_b]["signature"])
                    overlap = sig_a & sig_b
                    if len(overlap) >= 3:
                        self.duplicates.append({
                            "repo_a": name_a,
                            "repo_b": name_b,
                            "category": cat,
                            "overlap": sorted(overlap),
                            "overlap_score": len(overlap),
                            "repo_a_files": self.repos[name_a]["files_count"],
                            "repo_b_files": self.repos[name_b]["files_count"],
                        })

        self.duplicates.sort(key=lambda x: x["overlap_score"], reverse=True)
        print("Found %d potential duplicates" % len(self.duplicates))
        for d in self.duplicates[:25]:
            print("  [%d] %s <-> %s" % (d["overlap_score"], d["repo_a"], d["repo_b"]))
            print("       shared: %s" % ", ".join(d["overlap"]))

    def find_merge_candidates(self):
        print("\nAnalyzing merge groups...")

        known_groups = {
            "flux-runtime-group": [
                "flux-runtime", "flux-runtime-c", "flux-py", "flux-js",
                "flux-zig", "flux-wasm", "flux-core-rust", "flux-java",
                "flux-llama", "flux-swarm", "flux-simulator", "flux-visualizer",
                "flux-ide", "flux-coverage", "flux-cross-assembler",
                "flux-conf", "flux-evolve-py",
            ],
            "holodeck-group": [
                "holodeck-rust", "holodeck-studio", "holodeck-c", "holodeck-go",
                "holodeck-cuda", "holodeck-zig", "holodeck-tui",
            ],
            "fleet-infra-group": [
                "fleet-agent-api", "lighthouse-keeper", "fleet-mechanic",
                "fleet-github-app", "fleet-orchestrator", "fleet-dashboard",
            ],
            "agent-std-group": [
                "git-agent-standard", "dockside-exam", "agent-bootcamp",
                "z-bootcamp", "greenhorn-onboarding", "greenhorn-onboarding-deep",
            ],
            "i2i-group": [
                "iron-to-iron", "bottle-system", "flux-baton",
                "mesosynchronous", "fleet-liaison-tender",
            ],
            "cocapn-group": [
                "cocapn", "cocapn-runtime", "commodore-protocol",
            ],
            "skills-group": [
                "flux-skills", "agent-skills", "murmer-agent",
                "spreader-agent", "dream-engine",
            ],
            "research-group": [
                "abstraction-planes", "constraint-theory-core",
                "isa-v3-draft", "edge-research-relay",
            ],
            "brand-group": [
                "brand-assets", "fleet-english", "fleet-chinese", "fleet-arabic",
                "fleet-japanese", "fleet-sanskrit", "fleet-latin", "fleet-finnish",
                "fleet-navajo", "fleet-json-a2a",
            ],
        }

        for group_name, members in known_groups.items():
            existing = [m for m in members if m in self.repos]
            if len(existing) < 2:
                continue

            best = max(existing, key=lambda n: (
                self.repos[n]["has_tests"] * 100
                + self.repos[n]["has_ci"] * 50
                + self.repos[n]["files_count"]
            ))
            others = [n for n in existing if n != best]

            self.merge_candidates.append({
                "group": group_name,
                "canonical": best,
                "absorb": others,
                "existing_count": len(existing),
                "rationale": "%s has best score in %s" % (best, group_name),
            })

        print("Found %d merge groups" % len(self.merge_candidates))
        for mc in self.merge_candidates:
            print("\n  GROUP: %s (%d repos)" % (mc["group"], mc["existing_count"]))
            print("    Canonical: %s" % mc["canonical"])
            print("    Absorb: %s" % ", ".join(mc["absorb"]))

    def generate_report(self):
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "repos_scanned": len(self.repos),
            "categories": {k: len(v) for k, v in sorted(self.categories.items())},
            "duplicates_found": len(self.duplicates),
            "merge_groups": len(self.merge_candidates),
            "top_duplicates": self.duplicates[:25],
            "merge_candidates": self.merge_candidates,
            "uncategorized": self.categories.get("uncategorized", []),
            "all_repos": {
                name: {
                    "category": data["category"],
                    "files": data["files_count"],
                    "languages": data["languages"],
                    "has_tests": data["has_tests"],
                    "has_ci": data["has_ci"],
                    "signature": data["signature"],
                }
                for name, data in self.repos.items()
            },
        }

        path = "/home/ubuntu/.openclaw/workspace/research/refactor-report.json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Human-readable summary
        summary_path = "/home/ubuntu/.openclaw/workspace/research/refactor-summary.md"
        with open(summary_path, "w") as f:
            f.write("# Fleet Refactor Report\n\n")
            f.write("**Generated**: %s\n\n" % datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
            f.write("## Stats\n\n")
            f.write("- **Repos scanned**: %d\n" % report["repos_scanned"])
            f.write("- **Duplicates found**: %d\n" % report["duplicates_found"])
            f.write("- **Merge groups**: %d\n\n" % report["merge_groups"])
            f.write("## Categories\n\n")
            for cat, count in sorted(report["categories"].items(), key=lambda x: -x[1]):
                f.write("- **%s**: %d repos\n" % (cat, count))
            f.write("\n## Top Duplicates\n\n")
            for d in report["top_duplicates"][:15]:
                f.write("### [%d] %s <-> %s\n" % (d["overlap_score"], d["repo_a"], d["repo_b"]))
                f.write("- Shared: %s\n" % ", ".join(d["overlap"]))
                f.write("- Files: %d vs %d\n\n" % (d["repo_a_files"], d["repo_b_files"]))
            f.write("\n## Merge Groups\n\n")
            for mc in report["merge_candidates"]:
                f.write("### %s\n" % mc["group"])
                f.write("- **Canonical**: %s\n" % mc["canonical"])
                f.write("- **Absorb**: %s\n" % ", ".join(mc["absorb"]))
                f.write("- **Rationale**: %s\n\n" % mc["rationale"])

        print("\nReport saved:")
        print("  JSON: %s" % path)
        print("  Summary: %s" % summary_path)
        return report


if __name__ == "__main__":
    engine = FleetRefactorEngine()
    engine.scan()
    engine.find_duplicates()
    engine.find_merge_candidates()
    report = engine.generate_report()

    print("\n" + "=" * 50)
    print("FLEET REFACTOR REPORT")
    print("=" * 50)
    print("Repos scanned: %d" % report["repos_scanned"])
    print("Duplicates: %d" % report["duplicates_found"])
    print("Merge groups: %d" % report["merge_groups"])
    print("Uncategorized: %d" % len(report["uncategorized"]))
