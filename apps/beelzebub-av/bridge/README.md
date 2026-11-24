# Beelzebub AV Event Bridge

A small, standard-library-only Go receiver for the upstream Beelzebub v3 honeypot tracer. It is a local telemetry adapter, not a second honeypot and not a malware detector.

## Run

~~~sh
go test -race ./...
go vet ./...
go build -trimpath -o bav-bridge ./cmd/bav-bridge
./bav-bridge serve
~~~

DuckOS starts this process with the Beelzebub AV ingest command or from the Duck Desktop Beelzebub tab. The receiver listens on 127.0.0.1:9777 by default. It rejects non-loopback bind addresses. BAV_EVENT_ADDR may select another loopback address/port, BAV_DATA_DIR may select a custom data directory, and BAV_EVENT_TOKEN may supply a 32+ character bearer token. Without an environment token it creates a cryptographically random 256-bit token in ingest.token with owner-only permissions. Never copy the token into logs or screenshots.

## Upstream Beelzebub v3

The upstream runtime currently has tracer events and stdout, RabbitMQ and Cloud sinks, but no public event-sink plugin interface. Apply the companion patch-set documented under upstream/beelzebub-v3/ to add an opt-in event forwarder that preserves the existing sink. Configure it to POST the original tracer event as JSON to http://127.0.0.1:9777/v1/events with the bearer token read from ingest.token.

The loopback design is intended for the local Beelzebub binary or a deployment sharing the host network namespace (for example, an explicitly configured host-network lab). Ordinary Docker bridge networking does not route a container's 127.0.0.1 to a host process. Do not expose this intake endpoint to LAN/WAN interfaces. A remote deployment requires a separately designed authenticated TLS/mTLS transport and explicit egress policy.

## Privacy and event processing

The bridge validates JSON, requires the upstream protocol field, limits each request to 1 MiB, caps concurrent processing at 32 requests, and returns 202 Accepted only after a sanitized record is durably appended. It stores event time, protocol, response status, normalized source IP/port, hostname, HTTP method/path, SHA-256 digests, a bounded classification set and a severity label. It does not persist raw usernames, passwords, cookies, request headers, command text/output, raw binary commands, environment data or request bodies. Raw payloads exist only in request memory while hashes and heuristic labels are calculated.

Local signatures use the same text format as the Java scanner: SHA256|HIGH|label or SHA256|CRITICAL|label. The feed is read-only at startup, capped at 32 MiB and 250,000 indicators. The receiver does not update it or access the network.

Events are written as NDJSON in the Java application's data directory under events/. Per-file permissions are 0600, directories are owner-only where supported. Files rotate at 64 MiB with four files maximum per UTC day. This bridge produces honeypot behavioural telemetry, not a verdict that a file on the host is infected. It never scans, quarantines, deletes or executes user files.
