# Upstream Beelzebub v3 integration patch

The companion patch `0001-bav-event-forwarder.patch` adds an optional BAV event sink to the upstream Go runtime. It is designed for `beelzebub-labs/beelzebub` v3 at base commit:

`3f20be5355c7d6f144329e39c478cdd7ff98184c`

The patch is stored here as an upstream change-set; it does not vendor upstream Beelzebub source into DuckOS and does not modify the upstream GitHub repository automatically.

## Apply to an upstream checkout

~~~sh
git checkout 3f20be5355c7d6f144329e39c478cdd7ff98184c
PATCH=/path/to/DuckOS/apps/beelzebub-av/upstream/beelzebub-v3/0001-bav-event-forwarder.patch
git apply --check "$PATCH"
git apply "$PATCH"
gofmt -w internal/parser/configurations_parser.go internal/builder/builder.go internal/builder/director.go internal/builder/bav_event_forwarder.go internal/builder/bav_event_forwarder_test.go
go test ./internal/parser ./internal/builder
~~~

Re-check the patch if the upstream checkout is newer than the recorded base commit. The patch intentionally modifies the upstream project only after an operator applies it.

## Configure the optional sink

Start the DuckOS receiver first:

~~~sh
duckos beelzebub ingest
~~~

The receiver prints the path of its generated `ingest.token` file (not its contents). Configure Beelzebub using an owner-only token file:

~~~yaml
core:
  tracings:
    beelzebub-av:
      enabled: true
      endpoint: "http://127.0.0.1:9777/v1/events"
      auth-token-file: "/absolute/path/to/ingest.token"
      timeout-milliseconds: 750
~~~

Environment equivalents:
- `BEELZEBUB_AV_ENABLED=true`
- `BEELZEBUB_AV_ENDPOINT=http://127.0.0.1:9777/v1/events`
- `BEELZEBUB_AV_AUTH_TOKEN_FILE=/absolute/path/to/ingest.token`
- `BEELZEBUB_AV_TIMEOUT_MILLISECONDS=750`

The `auth-token` field or `BEELZEBUB_AV_AUTH_TOKEN` can supply the secret directly, but the file option is preferable. Avoid putting secrets in shell history or logs.

The upstream forwarder decorates (does not replace) the selected stdout, RabbitMQ or Beelzebub Cloud strategy. It enqueues events asynchronously in a bounded queue and does not block protocol workers when BAV is unavailable. Queue overflow and failed delivery are counted and reported without logging event contents. The receiver binds to a literal loopback IP only and the upstream client rejects non-loopback endpoints and redirects.

## Container networking

The default upstream Docker Compose deployment uses bridge networking. In that mode, `127.0.0.1` inside the Beelzebub container is the container itself, not the DuckOS host. Use the Go runtime on the same host/network namespace as the receiver, or design a separate authenticated TLS/mTLS transport for remote/container-network deployment. Do not expose the HTTP intake port to LAN/WAN.

## Data and interpretation

Honeypot events are attacker interactions with a decoy. A classification such as credential attempt, reconnaissance, suspicious download/execute command or HTTP path probe is behavioural evidence, not proof that the DuckOS host is infected. BAV stores only normalized metadata, hashes and classifications; raw credentials, command text/output, headers, cookies and request bodies are discarded. Honeypot events never run file scanning, deletion or quarantine actions.
