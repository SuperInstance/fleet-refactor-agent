# 🔧 Fleet Refactor Sub-Agents

> Continuous refactoring of JC1's repos into the Cocapn fleet paradigm.

## Repos Being Refactored (11)

| Repo | Language | Files | Missing | Priority | Novel |
|------|----------|-------|---------|----------|-------|
| capitaine | TypeScript | 147 | 3 | HIGH |  |
| ghost-tiles |  | 3 | 3 | HIGH | ⭐ |
| deckboss | TypeScript | 1524 | 1 | MEDIUM |  |
| api-gateway | Rust | 28 | 2 | MEDIUM |  |

## Papers Written
- [ghost-tiles/PAPER.md](https://github.com/SuperInstance/ghost-tiles/blob/main/PAPER.md)

## Refactor Process

1. **Fork** JC1's repos to SuperInstance
2. **Analyze** each repo for missing standards
3. **Push** CHARTER, REFACTOR-NOTES, fleet standards
4. **Refactor** into fleet paradigm (tests, CI, docs, I2I integration)
5. **Discover** novel insights → write papers
6. **Iterate** continuously as JC1 pushes new work

## The Loop

```
JC1 pushes code → Oracle1 forks → Refactor agents analyze
    → Standards applied → Tests added → Papers written
    → Insights fed back to fleet → JC1 sees improvements
    → JC1 builds on improvements → Cycle repeats
```

## Constraint

Refactor agents respect JC1's original work. They add fleet standards,
tests, and documentation without changing the core logic. Novel insights
are documented, not implemented — JC1 decides what to adopt.

*Cloud refactors, edge decides.*
