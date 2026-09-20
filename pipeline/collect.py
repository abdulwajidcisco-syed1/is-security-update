"""Bounded collectors for approved public RSS, NVD, and Hacker News sources."""
from datetime import datetime, timezone
import ipaddress
import json
import socket
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

from .config import public_url

USER_AGENT = "is-security-update/0.2 (+https://github.com/abdulwajidcisco-syed1/is-security-update)"
ALLOWED_HOSTS = {"www.cisa.gov", "raw.githubusercontent.com", "services.nvd.nist.gov", "hn.algolia.com"}

class CollectionError(RuntimeError):
    pass

def fetch(url: str, timeout: int = 20) -> bytes:
    public_url(url)
    host = (urlsplit(url).hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        raise CollectionError("Host is not allowlisted")
    try:
        addresses = {row[4][0] for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
        if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
            raise CollectionError("Host resolution is unsafe")
    except (OSError, ValueError) as exc:
        raise CollectionError("Source resolution failed") from exc
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/rss+xml, application/atom+xml"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=timeout) as response:
                if (urlsplit(response.geturl()).hostname or "").lower() not in ALLOWED_HOSTS:
                    raise CollectionError("Redirect left allowlist")
                data = response.read(5_000_001)
                if len(data) > 5_000_000:
                    raise CollectionError("Response too large")
                return data
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise CollectionError("Source request failed") from exc
        except OSError as exc:
            if attempt == 2:
                raise CollectionError("Source request failed") from exc
        time.sleep(attempt + 1)
    raise CollectionError("Source request failed")

def iso(value) -> str:
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    return datetime(*value[:6], tzinfo=timezone.utc).isoformat()

def collect_feed(source, retrieved: datetime) -> list[dict]:
    try:
        root = ElementTree.fromstring(fetch(source.url))
    except ElementTree.ParseError as exc:
        raise CollectionError("Malformed feed") from exc
    rows = []
    for entry in root.findall(".//item") + root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        def value(*names):
            for name in names:
                node = entry.find(name)
                if node is not None:
                    return node.get("href") or "".join(node.itertext()).strip()
            return ""
        published = value("pubDate", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated")
        link = value("link", "{http://www.w3.org/2005/Atom}link")
        if published and link:
            try:
                moment = parsedate_to_datetime(published) if "," in published else datetime.fromisoformat(published.replace("Z", "+00:00"))
                rows.append({"source_id": source.id, "url": link, "title": value("title", "{http://www.w3.org/2005/Atom}title") or "Untitled", "content": value("description", "{http://www.w3.org/2005/Atom}summary", "{http://www.w3.org/2005/Atom}content"), "published_at": moment.astimezone(timezone.utc).isoformat(), "retrieved_at": retrieved.isoformat()})
            except ValueError:
                continue
    return rows

def collect_cisa_kev(source, retrieved: datetime) -> list[dict]:
    payload = json.loads(fetch(source.url))
    rows = []
    for item in payload.get("vulnerabilities", []):
        cve_id = item.get("cveID")
        date_added = item.get("dateAdded")
        if not cve_id or not date_added:
            continue
        published = datetime.fromisoformat(date_added).replace(tzinfo=timezone.utc)
        vendor = item.get("vendorProject", "Unknown vendor")
        product = item.get("product", "Unknown product")
        description = item.get("shortDescription", "")
        action = item.get("requiredAction", "")
        rows.append({
            "source_id": source.id,
            "url": f"https://www.cisa.gov/known-exploited-vulnerabilities-catalog?field_cve={cve_id}",
            "title": f"{cve_id}: {vendor} {product}",
            "content": " ".join(part for part in (description, action) if part),
            "published_at": published.isoformat(),
            "retrieved_at": retrieved.isoformat(),
        })
    return rows
def collect_nvd(source, start: datetime, end: datetime, retrieved: datetime) -> list[dict]:
    query = urlencode({"pubStartDate": start.isoformat(timespec="milliseconds").replace("+00:00", "Z"), "pubEndDate": end.isoformat(timespec="milliseconds").replace("+00:00", "Z"), "resultsPerPage": 2000})
    payload = json.loads(fetch(f"{source.url}?{query}"))
    rows = []
    for wrapper in payload.get("vulnerabilities", []):
        cve = wrapper.get("cve", {})
        descriptions = [row.get("value", "") for row in cve.get("descriptions", []) if row.get("lang") == "en"]
        if descriptions:
            cve_id = cve.get("id", "Unknown CVE")
            rows.append({"source_id": source.id, "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}", "title": cve_id, "content": descriptions[0], "published_at": iso(cve.get("published")), "retrieved_at": retrieved.isoformat()})
    return rows

def collect_hn(source, start: datetime, end: datetime, retrieved: datetime) -> list[dict]:
    query = urlencode({"tags": "story", "numericFilters": f"created_at_i>={int(start.timestamp())},created_at_i<{int(end.timestamp())}", "hitsPerPage": 100})
    payload = json.loads(fetch(f"{source.url}?{query}"))
    rows = []
    for hit in payload.get("hits", []):
        title = hit.get("title") or "Untitled"
        rows.append({"source_id": source.id, "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}", "title": title, "content": title, "published_at": iso(hit.get("created_at")), "retrieved_at": retrieved.isoformat()})
    return rows

def collect_all(settings, start: datetime, end: datetime) -> tuple[list[dict], dict[str, str]]:
    retrieved = datetime.now(timezone.utc)
    records, outcomes = [], {}
    for source in settings.sources:
        if not source.enabled or source.adapter == "fixture":
            continue
        try:
            if source.adapter in {"rss", "atom"}:
                rows = collect_feed(source, retrieved)
            elif source.adapter == "cisa_kev":
                rows = collect_cisa_kev(source, retrieved)
            elif source.adapter == "nvd":
                rows = collect_nvd(source, start, end, retrieved)
            elif source.adapter == "hn":
                rows = collect_hn(source, start, end, retrieved)
            else:
                raise CollectionError("Unsupported adapter")
            records.extend(rows)
            outcomes[source.id] = "succeeded"
        except (CollectionError, ValueError, KeyError, json.JSONDecodeError) as exc:
            cause = exc.__cause__
            if isinstance(cause, HTTPError):
                reason = f"http_{cause.code}"
            elif isinstance(cause, ElementTree.ParseError):
                reason = "malformed_xml"
            elif isinstance(cause, OSError):
                reason = "network_error"
            else:
                reason = type(exc).__name__
            print(json.dumps({"event": "source_failed", "source_id": source.id, "reason": reason}), file=sys.stderr)
            outcomes[source.id] = "failed"
    if not outcomes or all(value == "failed" for value in outcomes.values()):
        raise CollectionError("All live sources failed")
    return records, outcomes
