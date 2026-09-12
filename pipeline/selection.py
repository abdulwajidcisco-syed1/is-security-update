"""Deterministic timestamp filtering, topic matching, and duplicate grouping."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .config import public_url


def timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Timestamp required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timestamp must include timezone")
    return result.astimezone(timezone.utc)


def canonical_url(value: str) -> str:
    parsed = urlsplit(public_url(value))
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}]
    return urlunsplit(("https", parsed.netloc.lower(), parsed.path or "/", urlencode(sorted(query)), ""))


def normalized_text(value: str) -> str:
    return " ".join(value.casefold().split())


def select_items(records: list, settings, window_end: datetime):
    start = window_end - timedelta(hours=24)
    sources = {s.id: s for s in settings.sources if s.enabled}
    accepted, quarantine = [], []
    for index, row in enumerate(records):
        try:
            if not isinstance(row, dict) or row.get("source_id") not in sources:
                raise ValueError("Unknown source")
            source = sources[row["source_id"]]
            title, content = row.get("title"), row.get("content")
            if not isinstance(title, str) or not title.strip() or not isinstance(content, str) or not content.strip():
                raise ValueError("Missing title/content")
            published = timestamp(row.get("published_at"))
            basis, effective = "published_at", published
            if row.get("material_update") is True:
                effective = timestamp(row.get("updated_at"))
                if effective < published:
                    raise ValueError("Update precedes publication")
                basis = "updated_at"
            retrieved = timestamp(row.get("retrieved_at"))
            if retrieved < effective:
                raise ValueError("Retrieval precedes effective timestamp")
            url = canonical_url(row.get("url"))
            if not start <= effective < window_end:
                continue
            searchable = normalized_text(title + " " + content)
            topics = [t for t in settings.topics if t.id in source.topics and any(re.search(r"(?<!\w)" + re.escape(normalized_text(alias)) + r"(?!\w)", searchable) for alias in t.aliases)]
            if not topics:
                continue
            score = sum(t.weight for t in topics) + source.priority
            if score < settings.minimum_score:
                continue
            evidence = {"source_id": source.id, "url": url, "published_at": published.isoformat(), "effective_at": effective.isoformat(), "timestamp_basis": basis, "retrieved_at": retrieved.isoformat(), "excerpt": content}
            accepted.append({"story_id": sha256(url.encode()).hexdigest()[:16], "title": title.strip(), "content": content, "url": url, "topics": [t.id for t in topics], "score": score, "effective_at": effective.isoformat(), "content_hash": sha256(normalized_text(content).encode()).hexdigest(), "evidence": [evidence]})
        except (ValueError, TypeError, KeyError):
            # Do not echo raw input or potentially secret-bearing URLs into logs.
            quarantine.append({"record_index": index, "reason": "invalid_metadata"})
    accepted.sort(key=lambda item: (-item["score"], -timestamp(item["effective_at"]).timestamp(), item["url"]))
    groups = []
    for item in accepted:
        matches = [g for g in groups if item["url"] in g["urls"] or item["content_hash"] in g["hashes"]]
        if matches:
            group = matches[0]
            for other in matches[1:]:
                group["urls"].update(other["urls"])
                group["hashes"].update(other["hashes"])
                group["story"]["evidence"].extend(other["story"]["evidence"])
                group["story"]["topics"] = sorted(set(group["story"]["topics"] + other["story"]["topics"]))
                groups.remove(other)
            group["urls"].add(item["url"])
            group["hashes"].add(item["content_hash"])
            group["story"]["evidence"].extend(item["evidence"])
            group["story"]["topics"] = sorted(set(group["story"]["topics"] + item["topics"]))
        else:
            groups.append({"urls": {item["url"]}, "hashes": {item["content_hash"]}, "story": item})
    selected = [g["story"] for g in groups[:settings.max_items]]
    for story in selected:
        story["evidence"] = list({(e["source_id"], e["url"], e["effective_at"]): e for e in story["evidence"]}.values())
    return selected, quarantine
