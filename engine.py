#!/usr/bin/env python3
"""
Fleet Refactor Engine — The Shipwright's Tools

Scans the SuperInstance fleet for:
1. Duplicate/overlapping repos
2. Superseded repos
3. Inconsistent standards
4. Merge candidates

Outputs merge proposals as structured JSON.
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
    """Get all repos for an org."""
    repos = []
    page = 1
    while True:
        data = api(f"https://api.github.com/orgs/{org}/repos?per_page={per_page}&page={page}&sort=updated")
        if not data: break
        repos.extend(data)
        page += 1
        if len(data) < per_page: break
    return repos

def get_tree(repo_full_name):
    """Get file tree for a repo."""
    try:
        data = api(f"https://api.github.com/repos/{repo_full_name}/git/trees/main?recursive=1")
        return [t["path"] for t in data.get("tree", []) if t["type"] == "blob"]
    except:
        try:
            data = api(f"https://api.github.com/repos/{repo_full_name}/git/trees/master?recursive=1")
            return [t["path"] for t in data.get("tree", []) if t["type"] == "blob"]
        except:
            return []

def extract_languages(files):
    """Extract programming languages from file extensions."""
    ext_map = {".py": "Python", ".rs": "Rust", ".go": "Go", ".c": "C", ".h": "C",
               ".js": "JavaScript", ".ts": "TypeScript", ".zig": "Zig", ".cu": "CUDA",
               ".java": "Java", ".md": "Markdown", ".json": "JSON", ".toml": "TOML",
               ".yml": "YAML", ".yaml": "YAML"}
    langs = set()
    for f in files:
        ext = os.path.splitext(f)[1]
        if ext in ext_map:
            langs.add(ext_map[ext])
    return list(langs)

def compute_signature(files):
    """Compute a signature for similarity detection based on key files."""
    key_patterns = ["vm", "runtime", "interpreter", "assembler", "compiler",
                    "opcode", "isa", "test", "mud", "holodeck", "agent",
                    "fleet", "keeper", "monitor", "mechanic", "bootcamp",
                    "skill", "flux", "signalk", "cocapn", "priority",
                    "camera", "anomaly", "twin", "capdb"]
    sig = []
    for f in files:
        fl = f.lower()
        for p in key_patterns:
            if p in fl:
                sig.append(p)
    return sorted(set(sig))

def categorize_repo(repo_data, files, signature):
    """Categorize a repo by its functional domain."""
    name = repo_data["name"].lower()
    desc = (repo_data.get("description") or "").lower()
    all_text = name + " " + desc + " " + " ".join(signature)
    
    categories = {
        "flux-runtime": ["flux", "vm", "runtime", "interpreter", "bytecode", "opcode", "isa"],
        "holodeck": ["holodeck", "mud", "room", "studio"],
        "fleet-infra": ["fleet", "agent-api", "keeper", "monitor", "mechanic"],
        "agent-std": ["git-agent", "standard", "dockside", "bootcamp", "charter"],
        "cocapn": ["cocapn", "signalk", "boat", "marine", "vessel", "captain"],
        "flux-skills": ["skill", "murmur", "spreader", "dream", "streamer"],
        "research": ["research", "experiment", "paper", "lock", "dcs"],
        "i2i": ["i2i", "iron", "bottle", "envelope", "protocol"],
        "brand": ["brand", "logo", "image", "cultural", "fleet-english"],
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
        """Scan the entire fleet."""
        print("Scanning SuperInstance fleet...")
        repos = get_all_repos("SuperInstance")
        print(f"Found {len(repos)} repos")
        
        for r in repos:
            if r.get("fork"): continue  # skip forks for now
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
                "files": files[:50],  # first 50 for reference
            }
            self.categories[category].append(name)
            time.sleep(0.3)
        
        print(f"Categorized {len(self.repos)} non-fork repos")
    
    def find_duplicates(self):
        """Find repos with overlapping signatures."""
        print("
Finding duplicates...")
        
        # Group by category
        for cat, repo_names in self.categories.items():
            if len(repo_names) < 2: continue
            
            # Compare signatures within category
            for i, name_a in enumerate(repo_names):
                for name_b in repo_names[i+1:]:
                    sig_a = set(self.repos[name_a]["signature"])
                    sig_b = set(self.repos[name_b]["signature"])
                    overlap = sig_a & sig_b
                    
                    if len(overlap) >= 3:  # significant overlap
                        self.duplicates.append({
                            "repo_a": name_a,
                            "repo_b": name_b,
                            "category": cat,
                            "overlap": list(overlap),
                            "overlap_score": len(overlap),
                            "repo_a_files": self.repos[name_a]["files_count"],
                            "repo_b_files": self.repos[name_b]["files_count"],
                        })
        
        self.duplicates.sort(key=lambda x: x["overlap_score"], reverse=True)
        print(f"Found {len(self.duplicates)} potential duplicates")
        
        for d in self.duplicates[:20]:
            print(f"  {d['overlap_score']:2d} overlap: {d['repo_a']:30s} ↔ {d['repo_b']}")
            print(f"             shared: {', '.join(d['overlap'])}")
    
    def find_merge_candidates(self):
        """Identify specific merge candidates."""
        print("
Analyzing merge candidates...")
        
        known_merges = {
            # FLUX runtimes in multiple languages
            "flux-runtime-group": ["flux-runtime", "flux-runtime-c", "flux-py", "flux-js", 
                                    "flux-zig", "flux-wasm", "flux-core-rust", "flux-java"],
            # Holodeck implementations
            "holodeck-group": ["holodeck-rust", "holodeck-studio", "holodeck-c", "holodeck-go",
                               "holodeck-cuda", "holodeck-zig", "holodeck-tui"],
            # Fleet infrastructure
            "fleet-infra-group": ["fleet-agent-api", "lighthouse-keeper", "fleet-mechanic",
                                   "fleet-github-app", "fleet-orchestrator"],
            # Agent standards
            "agent-std-group": ["git-agent-standard", "dockside-exam", "agent-bootcamp",
                                 "z-bootcamp"],
            # I2I/Communication
            "i2i-group": ["iron-to-iron", "bottle-system", "flux-baton", "mesosynchronous"],
            # Cocapn product
            "cocapn-group": ["cocapn", "cocapn-runtime", "commodore-protocol"],
            # Research
            "research-group": ["flux-skills", "abstraction-planes", "flux-cross-assembler"],
        }
        
        for group_name, members in known_merges.items():
            existing = [m for m in members if m in self.repos]
            if len(existing) < 2: continue
            
            # Find the "best" repo (most files, most recent, has tests)
            best = max(existing, key=lambda n: (
                self.repos[n]["has_tests"] * 100 + 
                self.repos[n]["has_ci"] * 50 +
                self.repos[n]["files_count"]
            ))
            
            others = [n for n in existing if n != best]
            
            self.merge_candidates.append({
                "group": group_name,
                "canonical": best,
                "absorb": others,
                "rationale": f"{best} has best test coverage and file count in the {group_name} group",
            })
        
        print(f"Found {len(self.merge_candidates)} merge groups")
        for mc in self.merge_candidates:
            print(f"
  📦 {mc['group']}")
            print(f"     Canonical: {mc['canonical']}")
            print(f"     Absorb: {', '.join(mc['absorb'])}")
    
    def generate_report(self):
        """Generate the full refactor report."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "repos_scanned": len(self.repos),
            "categories": {k: len(v) for k, v in self.categories.items()},
            "duplicates_found": len(self.duplicates),
            "merge_groups": len(self.merge_candidates),
            "top_duplicates": self.duplicates[:20],
            "merge_candidates": self.merge_candidates,
            "category_distribution": dict(self.categories),
            "uncategorized": self.categories.get("uncategorized", []),
        }
        
        path = "/home/ubuntu/.openclaw/workspace/research/refactor-report.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"
Report saved: {path}")
        return report

if __name__ == "__main__":
    engine = FleetRefactorEngine()
    engine.scan()
    engine.find_duplicates()
    engine.find_merge_candidates()
    report = engine.generate_report()
    
    print(f"
=== REFACTOR REPORT ===")
    print(f"  {report['repos_scanned']} repos scanned")
    print(f"  {report['duplicates_found']} potential duplicates")
    print(f"  {report['merge_groups']} merge groups identified")
    print(f"  Categories: {json.dumps(report['categories'])}")
