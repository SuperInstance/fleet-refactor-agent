```python
from datetime import datetime
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class RepoData:
    """Container for repository metadata used in merge scoring."""
    name: str
    files_count: int
    has_tests: bool
    has_ci: bool
    has_readme: bool
    has_charter: bool
    languages: List[str]
    last_push: datetime
    test_count: int
    description: str
    signature_keywords: List[str]

def merge_score(repo_a: RepoData, repo_b: RepoData) -> float:
    """
    Compute a merge compatibility score between two repositories.

    The score is a weighted sum of five components (total range 0.0‑1.0):
    - Code similarity (0.3): overlap of ``signature_keywords``.
    - Quality (0.25): average of boolean quality flags.
    - Activity (0.15): recency of the most recent push (capped at 1 year).
    - Size compatibility (0.1): similarity of ``files_count``.
    - Language overlap (0.2): shared programming languages.

    Args:
        repo_a: First repository.
        repo_b: Second repository.

    Returns:
        A float between 0.0 and 1.0 representing the merge suitability.
    """
    # 1. Code similarity
    kw_a = set(repo_a.signature_keywords)
    kw_b = set(repo_b.signature_keywords)
    overlap = len(kw_a & kw_b) / max(len(kw_a | kw_b), 1)
    code_score = 0.3 * overlap

    # 2. Quality
    quality_a = (repo_a.has_tests + repo_a.has_ci + repo_a.has_readme + repo_a.has_charter) / 4
    quality_b = (repo_b.has_tests + repo_b.has_ci + repo_b.has_readme + repo_b.has_charter) / 4
    quality_score = 0.25 * ((quality_a + quality_b) / 2)

    # 3. Activity (days since last push, newer = higher score)
    now = datetime.now()
    days_a = (now - repo_a.last_push).days
    days_b = (now - repo_b.last_push).days
    avg_days = (days_a + days_b) / 2
    activity_factor = max(0, 1 - avg_days / 365)  # linear decay over a year
    activity_score = 0.15 * activity_factor

    # 4. Size compatibility
    size_diff = abs(repo_a.files_count - repo_b.files_count)
    max_size = max(repo_a.files_count, repo_b.files_count, 1)
    size_score = 0.1 * (1 - size_diff / max_size)

    # 5. Language overlap
    lang_a = set(repo_a.languages)
    lang_b = set(repo_b.languages)
    lang_overlap = len(lang_a & lang_b) / max(len(lang_a | lang_b), 1)
    language_score = 0.2 * lang_overlap

    return code_score + quality_score + activity_score + size_score + language_score

def classify_merge(score: float) -> str:
    """
    Classify the merge decision based on the computed score.

    - ``auto_merge`` : score > 0.8
    - ``propose``    : 0.5 < score ≤ 0.8
    - ``monitor``    : 0.3 < score ≤ 0.5
    - ``ignore``     : score ≤ 0.3

    Args:
        score: Merge score from :func:`merge_score`.

    Returns:
        A string label indicating the recommended action.
    """
    if score > 0.8:
        return "auto_merge"
    if score > 0.5:
        return "propose"
    if score > 0.3:
        return "monitor"
    return "ignore"

def score_all_pairs(repos: List[RepoData]) -> List[Tuple[RepoData, RepoData, float, str]]:
    """
    Evaluate every unique pair of repositories.

    For each unordered pair (i, j) where i < j, compute the merge score
    and its classification.

    Args:
        repos: List of :class:`RepoData` objects.

    Returns:
        A list of tuples ``(repo_a, repo_b, score, classification)``.
    """
    results: List[Tuple[RepoData, RepoData, float, str]] = []
    for i in range(len(repos)):
        for j in range(i + 1, len(repos)):
            a, b = repos[i], repos[j]
            s = merge_score(a, b)
            results.append((a, b, s, classify_merge(s)))
    return results
```