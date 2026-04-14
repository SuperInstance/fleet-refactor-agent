# BOOTCAMP — Fleet Refactor Agent

## Training Path

### Level 1: Scanner
- Scan all SuperInstance repos
- Extract metadata: languages, files, signatures
- Categorize by functional domain
- **Test**: Correctly categorize 50 repos with 90% accuracy

### Level 2: Duplicate Detector
- Compare repos within categories
- Detect functional overlap via file/function analysis
- Score overlap significance
- **Test**: Find 10 known duplicates in a test set

### Level 3: Merge Planner
- Given two overlapping repos, generate merge strategy
- Identify best parts of each (tests, docs, implementations)
- Produce step-by-step merge plan
- **Test**: Plan merge of two test repos without data loss

### Level 4: Auto-Merger
- Execute simple merges automatically (file moves, doc consolidation)
- Create PRs for review
- Update all cross-references
- **Test**: Merge two test repos and verify no broken links

### Level 5: Fleet Architect
- Identify architectural improvements across the fleet
- Propose repo reorganization for clarity
- Maintain fleet health score over time
- **Test**: Improve fleet average dockside score by 10%

## Constraints
- NEVER delete without archiving
- ALWAYS preserve git history
- ALWAYS run tests after merge
- ALWAYS update references in other repos
- ALWAYS create issue/PR for review before merging
