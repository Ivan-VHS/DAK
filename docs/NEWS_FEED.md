# Газета — Mora news feed

## Scope and implementation status

Газета is a first-party Mora application with a separate skeuomorphic newspaper surface. The browser implementation is partial and uses a public external data provider. The DAK `dak.news` application and `dak.news-feed.v1` service are design-catalog entries only; no native daemon, package, IPC endpoint or boot-image integration is implemented.

Implementation paths:

- `mora/news.js` — app markup, DOM rendering, interactions and local storage.
- `mora/news-core.js` — topic queries, safe URL normalization, timestamps and result bounds.
- `mora/app.js` — launcher identity, panel routing and app initialization.
- `mora/index.html` — desktop tile and dock entry.
- `mora/styles.css` — scoped paper-print design.

## Provider contract

The app requests `https://api.gdeltproject.org/api/v2/doc/doc` using `mode=artlist`, `format=json`, `maxrecords=30`, `timespan=24h` and `sort=datedesc`. The six built-in sections are Ukraine, Dnipro, World, Technology, Economy and Science. A user search is trimmed, stripped of control characters and query delimiters, limited to 100 characters and appended as a quoted phrase.

GDELT DOC 2.0 documents JSON/JSONP output, wildcard CORS support and search across machine-translated coverage in 65 languages. See the [official DOC 2.0 API introduction](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/). Results are an aggregation of publisher metadata; this app does not ingest full article bodies.

## Browser behavior

- Requests are made when the app opens, a section changes, a search is submitted or the user explicitly refreshes. There is no background polling.
- A client-wide 5.5-second request interval and a 15-second fetch timeout limit repeated calls.
- Only HTTPS article and image URLs are retained. Publisher links open in a new tab with `noopener`, `noreferrer` and `nofollow`; no referrer is sent.
- DOM text is inserted through `textContent`; titles and publisher metadata are not interpolated into HTML.
- The current profile caches up to eight result sets and stores up to 100 bookmarks. Storage keys are namespaced under `duckos.mora.news.*`.
- When the network is unavailable, the last saved result set and bookmarks remain available. The service worker caches the app modules, not external news data.

## Privacy and editorial boundaries

The browser sends the selected topic/search query to GDELT. Requests omit credentials and referrers, but the provider necessarily receives the network request and ordinary connection metadata. Queries and article bookmarks are stored locally in the current browser profile; they are not synchronized. Clearing that profile's site data removes the cache and saved bookmarks.

The feed does not claim that a source is trustworthy, does not fact-check headlines, does not generate summaries, does not scrape paywalled article text and does not bypass publisher access controls. Users should open the original publisher page and assess the reporting themselves. GDELT coverage may be incomplete and results can include duplicate, stale or irrelevant matches.

## Native DAK boundary

The DAK catalog declares `dak.news` with `dak.news-feed.v1`, `dak.network.v1` and `dak.vfs.v1` dependencies, plus separate network/source/bookmark permissions. These are proposed identifiers in a catalog whose suite status remains `design`. Before calling this a native DuckOS service, the project still needs a registered API/schema, a permission-enforcing network client, provider lifecycle, timeouts/retry/cancellation semantics, durable storage policy, notifications and target-image packaging tests.

## Validation

Run the browser-shell and news helper tests with Node.js 18 or newer:

```sh
npm test
```

Run the catalogue tests with the repository's Python test dependencies:

```sh
python -m unittest tests.test_app_catalog tests.test_dak_base_catalog -v
```

