package store

import (
	"crypto/sha256"
	"encoding/hex"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/ivan-vhs/duckos-beelzebub-av-bridge/internal/eventintel"
)

func TestAppendPersistsSanitizedNDJSON(t *testing.T) {
	root:=filepath.Join(t.TempDir(),"events")
	s,err:=New(root,"");if err!=nil {t.Fatal(err)}
	record:=eventintel.Record{Schema:"duckos.beelzebub-av-event.v1",ReceivedAt:time.Now().UTC().Format(time.RFC3339Nano),Protocol:"SSH",Severity:"LOW",SourceIP:"203.0.113.7",Classifications:[]string{"credential-attempt"}}
	if err:=s.Append(record);err!=nil {t.Fatal(err)}
	entries,err:=os.ReadDir(root);if err!=nil {t.Fatal(err)}
	if len(entries)!=1 {t.Fatalf("expected one event file, got %d",len(entries))}
	info,err:=entries[0].Info();if err!=nil {t.Fatal(err)}
	if info.Mode().Perm()!=0o600 {t.Fatalf("event file mode=%o",info.Mode().Perm())}
	data,err:=os.ReadFile(filepath.Join(root,entries[0].Name()));if err!=nil {t.Fatal(err)}
	if !strings.Contains(string(data),`"source_ip":"203.0.113.7"`) {t.Fatalf("missing sanitized IP: %s",data)}
	if !strings.HasSuffix(string(data),"\n") {t.Fatal("NDJSON record must end with newline")}
}
func TestLoadSignaturesAndLookup(t *testing.T) {
	payload:="indicator payload";sum:=sha256.Sum256([]byte(payload));hash:=hex.EncodeToString(sum[:])
	feed:=filepath.Join(t.TempDir(),"signatures.local")
	if err:=os.WriteFile(feed,[]byte(hash+"|CRITICAL|test-family\n"),0o600);err!=nil {t.Fatal(err)}
	s,err:=New(filepath.Join(t.TempDir(),"events"),feed);if err!=nil {t.Fatal(err)}
	indicator,ok:=s.LookupIndicator(hash)
	if !ok||indicator.Severity!="CRITICAL"||indicator.Label!="test-family" {t.Fatalf("unexpected indicator: %+v %v",indicator,ok)}
}
func TestRejectSymlinkedEventDirectory(t *testing.T) {
	base:=t.TempDir();target:=filepath.Join(base,"target")
	if err:=os.Mkdir(target,0o700);err!=nil {t.Fatal(err)}
	link:=filepath.Join(base,"link")
	if err:=os.Symlink(target,link);err!=nil {t.Skipf("symlink unavailable: %v",err)}
	if _,err:=New(link,"");err==nil {t.Fatal("expected symlink rejection")}
}
