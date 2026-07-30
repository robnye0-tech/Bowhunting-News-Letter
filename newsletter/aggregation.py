import hashlib
import re
from datetime import datetime
from datetime import timezone as dt_timezone
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from django.utils.text import slugify

from .models import ContentItem

TAG_RE = re.compile(r"<[^>]+>")

# Some state sites' basic bot protection rejects any request that doesn't
# look like a normal browser. This is a personal, low-frequency (every few
# hours at most) reader of public press-release pages, not a scraper trying
# to evade anything — a realistic browser header set is enough to get past
# simple User-Agent filtering.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def strip_tags(raw: str) -> str:
    return TAG_RE.sub("", raw or "").strip()


def process_rss_source(source, week_of):
    """Fetch an RSS/Atom feed and create draft ContentItems for new entries.

    Returns (created_count, error_message_or_None).
    """
    try:
        feed = feedparser.parse(source.url)
    except Exception as exc:
        return 0, f"failed to fetch: {exc}"

    if feed.bozo and not feed.entries:
        return 0, "could not parse feed"

    created = 0
    for entry in feed.entries:
        link = getattr(entry, "link", "")
        title = getattr(entry, "title", "").strip()
        if not link or not title:
            continue
        if ContentItem.objects.filter(state=source.state, url=link).exists():
            continue

        published_at = None
        if getattr(entry, "published_parsed", None):
            published_at = datetime(*entry.published_parsed[:6], tzinfo=dt_timezone.utc)

        ContentItem.objects.create(
            state=source.state,
            source=source,
            title=title,
            url=link,
            summary=strip_tags(getattr(entry, "summary", ""))[:2000],
            published_at=published_at,
            week_of=week_of,
        )
        created += 1

    return created, None


def process_page_source(source, week_of, output_root):
    """Fetch a plain page; if its visible text changed since the last check,
    write a snapshot file for human review and create a draft ContentItem.

    This is a generic change-detection watcher, not a smart content
    classifier — every state agency site is laid out differently, so it
    just flags "this page changed" and leaves reading/categorizing it to a
    human. The first time a source is checked there's nothing to compare
    against yet, so it only records a baseline snapshot.

    Returns (changed: bool, error_message_or_None).
    """
    try:
        response = requests.get(source.url, headers=REQUEST_HEADERS, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        return False, str(exc)

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())

    if not text:
        return False, "page had no readable text (may require JavaScript)"

    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    is_first_check = not source.last_seen_hash
    changed = source.last_seen_hash != content_hash

    source.last_seen_hash = content_hash
    source.last_checked_at = timezone.now()
    source.save(update_fields=["last_seen_hash", "last_checked_at"])

    if is_first_check:
        _write_snapshot(output_root, source, text, note="Baseline snapshot (first check, nothing to compare yet).")
        return False, None

    if not changed:
        return False, None

    _write_snapshot(output_root, source, text, note="Page content changed since the last check.")

    ContentItem.objects.get_or_create(
        state=source.state,
        url=source.url,
        week_of=week_of,
        defaults={
            "source": source,
            "title": f"{source.label} — page updated",
            "summary": text[:500],
        },
    )
    return True, None


def _write_snapshot(output_root, source, text, note):
    state_dir = Path(output_root) / source.state.code
    state_dir.mkdir(parents=True, exist_ok=True)

    timestamp = timezone.now().strftime("%Y-%m-%d_%H%M")
    filename = f"{timestamp}_{slugify(source.label)[:60] or 'source'}.md"
    path = state_dir / filename

    path.write_text(
        f"# {source.label}\n\n"
        f"State: {source.state.name}\n"
        f"Source URL: {source.url}\n"
        f"Checked: {timezone.now().isoformat()}\n"
        f"Note: {note}\n\n"
        f"---\n\n"
        f"{text[:8000]}\n",
        encoding="utf-8",
    )
