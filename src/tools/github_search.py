"""문서에 답이 없을 때 쓰는 보조 도구: GitHub 이슈/PR 검색."""
import requests

from .. import config

SEARCH_URL = "https://api.github.com/search/issues"


def search_github_issues(query: str, top_k: int = 3) -> list[dict]:
    headers = {"Accept": "application/vnd.github+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"

    params = {
        "q": f"repo:{config.GITHUB_REPO} {query} in:title,body",
        "per_page": top_k,
        "sort": "reactions",
        "order": "desc",
    }

    try:
        resp = requests.get(SEARCH_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except Exception as e:
        return [{"error": f"{type(e).__name__}: {e}"}]

    results = []
    for item in items[:top_k]:
        body = (item.get("body") or "").strip().replace("\n", " ")
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("html_url", ""),
                "state": item.get("state", ""),
                "snippet": body[:400],
            }
        )
    return results
