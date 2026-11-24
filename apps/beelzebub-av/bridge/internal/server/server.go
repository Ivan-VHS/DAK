package server

import (
	"crypto/subtle"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"mime"
	"net"
	"net/http"
	"strings"
	"sync/atomic"
	"time"

	"github.com/ivan-vhs/duckos-beelzebub-av-bridge/internal/eventintel"
	"github.com/ivan-vhs/duckos-beelzebub-av-bridge/internal/store"
)

const maxRequestBytes = 1 << 20

type Config struct {
	Address string
	Token   string
	Store   *store.Store
}

type Server struct {
	httpServer *http.Server
	token      []byte
	store      *store.Store
	inFlight   chan struct{}
	received   atomic.Uint64
	rejected   atomic.Uint64
}

func New(config Config) (*Server, error) {
	if config.Store == nil { return nil, errors.New("BAV event store is required") }
	if len(config.Token) < 32 { return nil, errors.New("BAV event token must contain at least 32 bytes") }
	if config.Address == "" { config.Address = "127.0.0.1:9777" }
	host, _, err := net.SplitHostPort(config.Address)
	if err != nil { return nil, fmt.Errorf("invalid BAV listen address: %w", err) }
	ip := net.ParseIP(host)
	if ip == nil || !ip.IsLoopback() { return nil, errors.New("BAV event receiver must bind to a loopback IP address only") }

	s := &Server{token: []byte(config.Token), store: config.Store, inFlight: make(chan struct{}, 32)}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", s.health)
	mux.HandleFunc("POST /v1/events", s.receive)
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) { http.NotFound(w, r) })
	s.httpServer = &http.Server{
		Addr: config.Address, Handler: mux, ReadHeaderTimeout: 2*time.Second,
		ReadTimeout: 5*time.Second, WriteTimeout: 5*time.Second, IdleTimeout: 30*time.Second,
		MaxHeaderBytes: 16 << 10,
	}
	return s, nil
}

func (s *Server) Handler() http.Handler { return s.httpServer.Handler }
func (s *Server) ListenAndServe() error { return s.httpServer.ListenAndServe() }
func (s *Server) Shutdown(timeout time.Duration) error {
	ctx, cancel := contextWithTimeout(timeout)
	defer cancel()
	return s.httpServer.Shutdown(ctx)
}
func (s *Server) Counts() (uint64, uint64) { return s.received.Load(), s.rejected.Load() }

func (s *Server) health(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{
		"schema": "duckos.beelzebub-av-bridge-health.v1", "status": "ok",
		"received": s.received.Load(), "rejected": s.rejected.Load(),
	})
}

func (s *Server) receive(w http.ResponseWriter, r *http.Request) {
	mediaType, _, mediaErr := mime.ParseMediaType(r.Header.Get("Content-Type"))
	if mediaErr != nil || mediaType != "application/json" {
		s.reject(w, http.StatusUnsupportedMediaType, "application/json is required")
		return
	}
	header := r.Header.Get("Authorization")
	provided := strings.TrimPrefix(header, "Bearer ")
	if provided == header || subtle.ConstantTimeCompare([]byte(provided), s.token) != 1 {
		s.reject(w, http.StatusUnauthorized, "invalid bearer token")
		return
	}
	select {
	case s.inFlight <- struct{}{}:
		defer func() { <-s.inFlight }()
	default:
		s.reject(w, http.StatusTooManyRequests, "event intake is busy")
		return
	}

	body := http.MaxBytesReader(w, r.Body, maxRequestBytes)
	defer body.Close()
	decoder := json.NewDecoder(body)
	var incoming eventintel.HoneypotEvent
	if err := decoder.Decode(&incoming); err != nil {
		var tooLarge *http.MaxBytesError
		if errors.As(err, &tooLarge) { s.reject(w, http.StatusRequestEntityTooLarge, "event exceeds 1 MiB"); return }
		s.reject(w, http.StatusBadRequest, "invalid event JSON")
		return
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		s.reject(w, http.StatusBadRequest, "event body must contain one JSON object")
		return
	}
	if incoming.Protocol == "" { s.reject(w, http.StatusBadRequest, "event protocol is required"); return }

	now := time.Now().UTC()
	record := s.store.Enrich(incoming, now)
	if err := s.store.Append(record); err != nil {
		s.reject(w, http.StatusServiceUnavailable, "event could not be durably stored")
		return
	}
	s.received.Add(1)
	writeJSON(w, http.StatusAccepted, map[string]any{
		"schema": "duckos.beelzebub-av-ingest-ack.v1", "accepted": true,
		"event_id": record.EventID, "stored_at": record.ReceivedAt,
	})
}

func (s *Server) reject(w http.ResponseWriter, code int, message string) {
	s.rejected.Add(1)
	writeJSON(w, code, map[string]string{"error": message})
}
func writeJSON(w http.ResponseWriter, code int, value any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(value)
}
