package store

import (
	"bufio"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/ivan-vhs/duckos-beelzebub-av-bridge/internal/eventintel"
)

const (
	maxFeedBytes  = 32 << 20
	maxIndicators = 250_000
	maxDailyFile  = 64 << 20
	maxDailyFiles = 4
)

type Store struct {
	root       string
	mu         sync.Mutex
	indicators map[string]eventintel.Indicator
}

func New(root, signatureFile string) (*Store, error) {
	if root == "" { return nil, fmt.Errorf("event store directory is required") }
	if err := os.MkdirAll(root, 0o700); err != nil { return nil, fmt.Errorf("create event store: %w", err) }
	if err := rejectSymlink(root); err != nil { return nil, err }
	if err := os.Chmod(root, 0o700); err != nil { return nil, fmt.Errorf("secure event store directory: %w", err) }
	s := &Store{root: root, indicators: make(map[string]eventintel.Indicator)}
	if signatureFile != "" { if err := s.loadSignatures(signatureFile); err != nil { return nil, err } }
	return s, nil
}

func (s *Store) LookupIndicator(hash string) (eventintel.Indicator, bool) {
	indicator, ok := s.indicators[strings.ToLower(hash)]
	return indicator, ok
}
func (s *Store) Enrich(input eventintel.HoneypotEvent, now time.Time) eventintel.Record {
	return eventintel.Enrich(input, now, s.indicators)
}

func (s *Store) Append(record eventintel.Record) error {
	line := eventintel.RecordJSON(record)
	if len(line) > 48<<10 { return fmt.Errorf("normalized event exceeds 48 KiB") }
	line += "\n"
	day := time.Now().UTC().Format("2006-01-02")
	s.mu.Lock()
	defer s.mu.Unlock()
	for index := 0; index < maxDailyFiles; index++ {
		name := fmt.Sprintf("events-%s-%03d.ndjson", day, index)
		path := filepath.Join(s.root, name)
		if err := rejectExistingSymlink(path); err != nil { return err }
		file, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o600)
		if err != nil { return fmt.Errorf("open event log: %w", err) }
		info, statErr := file.Stat()
		if statErr != nil { file.Close(); return fmt.Errorf("stat event log: %w", statErr) }
		if info.Size()+int64(len(line)) > maxDailyFile { file.Close(); continue }
		writer := bufio.NewWriter(file)
		_, writeErr := writer.WriteString(line)
		if writeErr == nil { writeErr = writer.Flush() }
		if writeErr == nil { writeErr = file.Sync() }
		closeErr := file.Close()
		if writeErr != nil { return fmt.Errorf("persist event log: %w", writeErr) }
		if closeErr != nil { return fmt.Errorf("close event log: %w", closeErr) }
		return nil
	}
	return fmt.Errorf("daily event log rotation limit reached")
}

func (s *Store) loadSignatures(filename string) error {
	if err := rejectExistingSymlink(filename); err != nil { return err }
	info, err := os.Stat(filename)
	if err != nil { if os.IsNotExist(err) { return nil }; return err }
	if info.Size() > maxFeedBytes { return fmt.Errorf("signature feed exceeds 32 MiB") }
	file, err := os.Open(filename)
	if err != nil { return err }
	defer file.Close()
	scanner := bufio.NewScanner(file)
	scanner.Buffer(make([]byte, 4096), 1024)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") { continue }
		parts := strings.SplitN(line, "|", 3)
		if len(parts) != 3 || len(parts[0]) != 64 { continue }
		if _, err := hex.DecodeString(parts[0]); err != nil { continue }
		severity := strings.ToUpper(parts[1])
		if severity != "HIGH" && severity != "CRITICAL" { continue }
		hash := strings.ToLower(parts[0])
		if _, exists := s.indicators[hash]; !exists && len(s.indicators) >= maxIndicators {
			return fmt.Errorf("signature feed exceeds 250,000 indicators")
		}
		s.indicators[hash] = eventintel.Indicator{SHA256: hash, Severity: severity, Label: safeLabel(parts[2])}
	}
	return scanner.Err()
}

func safeLabel(value string) string {
	value = strings.Map(func(r rune) rune { if r < 0x20 || r == 0x7f { return -1 }; return r }, strings.TrimSpace(value))
	if len(value) > 120 { return value[:120] }
	return value
}
func rejectSymlink(path string) error {
	info, err := os.Lstat(path)
	if err != nil { return err }
	if info.Mode()&os.ModeSymlink != 0 || !info.IsDir() { return fmt.Errorf("event store path must be a real directory") }
	return nil
}
func rejectExistingSymlink(path string) error {
	info, err := os.Lstat(path)
	if err != nil { if os.IsNotExist(err) { return nil }; return err }
	if info.Mode()&os.ModeSymlink != 0 || !info.Mode().IsRegular() { return fmt.Errorf("refusing non-regular file") }
	return nil
}
