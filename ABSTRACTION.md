# ABSTRACTION.md — Fleet Refactor Agent

## Primary Plane
Plane 4 (Domain) — repo analysis expressed in fleet vocabulary, decisions made through structured comparison

## Key Operations
- scan: enumerate repos, extract metadata
- compare: detect overlap via file/function/test similarity
- plan: generate merge strategy
- execute: create PRs, move files, update references
- verify: run dockside exam on merged result
