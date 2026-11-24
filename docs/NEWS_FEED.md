# Gazette news feed

Gazette is a separate editorial reader in Mora. It does not reuse the OS notification stream and does not change the shared DuckOS desktop palette. Its application surface uses tactile parchment, printed-ink typography, rules and paper-edge depth as a scoped skeuomorphic reading material.

## Included public feeds

| Section | Publisher | RSS feed |
|---|---|---|
| Ukraine | Українська правда | https://www.pravda.com.ua/rss/ |
| Ukraine | Суспільне Новини | https://suspilne.media/rss/ukrnet.rss |
| Ukraine | BBC News Україна | https://feeds.bbci.co.uk/ukrainian/rss.xml |
| Ukraine | The Kyiv Independent | https://kyivindependent.com/news-archive/rss/ |
| World | BBC World | https://feeds.bbci.co.uk/news/world/rss.xml |
| Technology | BBC Technology | https://feeds.bbci.co.uk/news/technology/rss.xml |

The source list is explicit and version-controlled in mora/news-feed.js. Gazette keeps publisher attribution beside each item and sends readers to the publisher's page for the full story. It displays short feed excerpts rather than reproducing full articles.

## Data flow

1. Mora requests each configured public RSS URL through https://api.rss2json.com/v1/api.json.
2. The converter response is treated as untrusted input. Titles and excerpts are reduced to bounded plain text, only HTTP(S) article links are accepted, and rendering uses DOM textContent; feed HTML is never inserted into the page.
3. Results are deduplicated by article URL, sorted by publication time and capped at 60 headline records.
4. Search and topic filters run locally. Bookmarks and the normalized headline cache are stored in the current browser profile.
5. A 15-minute cache window avoids repeat requests on every app open. A manual refresh bypasses that window. When some feeds fail, Gazette retains cached items for those publishers; when all feeds fail, it shows the last saved data and the source links.

## Privacy and boundaries

- The RSS-to-JSON converter is a third-party service. It receives the feed URLs requested by the browser and may observe request metadata. This service is not operated by DuckOS.
- Bookmark URLs and cached headline metadata are stored locally in localStorage. They are not sent to the converter.
- Network requests are made only when Gazette is opened without a fresh cache or when the user activates Refresh. No background polling is used.
- Mora Sentinel currently stores preferences and does not enforce process-level or per-app network isolation. Gazette therefore does not claim native capability-broker enforcement.
- Offline mode can show cached headlines, publisher/source labels and bookmarks; full article pages still require the publisher site to be reachable.
- RSS content and source availability are not guaranteed. Gazette does not certify the accuracy, impartiality or identity of a publisher and does not create original reporting.

The browser application has no credentials or API key embedded in the repository. The converter's availability and rate limits are external dependencies; failures are surfaced in the interface instead of being silently presented as complete coverage.
