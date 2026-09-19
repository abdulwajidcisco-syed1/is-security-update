"""Strict configuration for the initial, offline collection milestone."""

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
import ipaddress
import re

import yaml


class ConfigError(ValueError):
    pass


def public_url(value: str) -> str:
    """Validate a public-shaped HTTPS URL; not an SSRF-safe network resolver."""
    if not isinstance(value, str):
        raise ConfigError("URL must be a string")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ConfigError("Only HTTPS URLs without credentials are allowed")
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith((".local", ".localhost", ".internal")) or "." not in host:
        raise ConfigError("Private/local source hosts are not allowed")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        if not address.is_global:
            raise ConfigError("Private source addresses are not allowed")
    return value


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ConfigError("Invalid identifier")
    return value


def integer(value, minimum, maximum, field):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ConfigError(f"{field} must be an integer from {minimum} to {maximum}")
    return value


def read_yaml(path: Path):
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError("Cannot read configuration") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ConfigError("Configuration schema_version must be 1")
    return data


@dataclass(frozen=True)
class Topic:
    id: str
    aliases: tuple[str, ...]
    weight: int


@dataclass(frozen=True)
class Source:
    id: str
    url: str
    adapter: str
    enabled: bool
    topics: tuple[str, ...]
    priority: int
    verified_public: bool


@dataclass(frozen=True)
class Settings:
    show_id: str
    timezone: str
    max_items: int
    minimum_score: int
    topics: tuple[Topic, ...]
    sources: tuple[Source, ...]


def load_settings(show_path: Path, sources_path: Path) -> Settings:
    show, feeds = read_yaml(show_path), read_yaml(sources_path)
    # Publication is intentionally unavailable until editorial and media gates exist.
    if show.get("publishing_enabled") is not False:
        raise ConfigError("This milestone requires publishing_enabled: false")
    if show.get("timezone") != "UTC":
        raise ConfigError("Only UTC development editions are supported in this milestone")
    if not isinstance(show.get("topics"), list) or not show["topics"]:
        raise ConfigError("At least one topic is required")
    topics = []
    for row in show["topics"]:
        if not isinstance(row, dict):
            raise ConfigError("Invalid topic")
        aliases = row.get("aliases")
        if not isinstance(aliases, list) or not aliases or any(not isinstance(a, str) or not a.strip() for a in aliases):
            raise ConfigError("Topic aliases must be non-empty strings")
        topics.append(Topic(identifier(row.get("id")), tuple(aliases), integer(row.get("weight"), 1, 10, "weight")))
    topic_ids = {t.id for t in topics}
    if len(topic_ids) != len(topics):
        raise ConfigError("Duplicate topic identifiers")
    if not isinstance(feeds.get("sources"), list):
        raise ConfigError("sources must be a list")
    sources = []
    for row in feeds["sources"]:
        if not isinstance(row, dict):
            raise ConfigError("Invalid source")
        if type(row.get("enabled")) is not bool or type(row.get("verified_public")) is not bool:
            raise ConfigError("Source flags must be booleans")
        source_topics = row.get("topics")
        if not isinstance(source_topics, list) or not source_topics or any(t not in topic_ids for t in source_topics):
            raise ConfigError("Source references unknown or empty topics")
        if row.get("adapter") not in {"fixture", "rss", "atom", "nvd", "hn"}:
            raise ConfigError("Unsupported source adapter")
        if row["enabled"] and row["adapter"] != "fixture" and not row["verified_public"]:
            raise ConfigError("Live sources must be verified before enabling")
        sources.append(Source(identifier(row.get("id")), public_url(row.get("url")), row["adapter"], row["enabled"], tuple(source_topics), integer(row.get("priority"), 0, 10, "priority"), row["verified_public"]))
    if len({s.id for s in sources}) != len(sources):
        raise ConfigError("Duplicate source identifiers")
    if not any(s.enabled for s in sources):
        raise ConfigError("At least one source must be enabled")
    return Settings(identifier(show.get("show_id")), show["timezone"], integer(show.get("max_items"), 1, 100, "max_items"), integer(show.get("minimum_score"), 1, 100, "minimum_score"), tuple(topics), tuple(sources))
