package main

import (
	"crypto/rand"
	"encoding/base64"
	"errors"
	"fmt"
	"net"
	"os"
	"os/signal"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"time"

	"github.com/ivan-vhs/duckos-beelzebub-av-bridge/internal/server"
	"github.com/ivan-vhs/duckos-beelzebub-av-bridge/internal/store"
)

func main() {
	if len(os.Args) > 1 && os.Args[1] == "--version" {
		fmt.Println("Beelzebub AV bridge 1.0.0")
		return
	}
	if len(os.Args) > 1 && os.Args[1] != "serve" {
		fmt.Fprintln(os.Stderr, "usage: bav-bridge [serve|--version]")
		os.Exit(2)
	}
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, "bav-bridge:", err)
		os.Exit(1)
	}
}

func run() error {
	dataDir, err := dataDirectory()
	if err != nil { return err }
	if err := os.MkdirAll(dataDir, 0o700); err != nil { return fmt.Errorf("create BAV data directory: %w", err) }
	if err := rejectSymlink(dataDir); err != nil { return err }
	if runtime.GOOS != "windows" { if err := os.Chmod(dataDir, 0o700); err != nil { return err } }
	token, tokenPath, err := loadOrCreateToken(filepath.Join(dataDir, "ingest.token"))
	if err != nil { return err }
	storePath := filepath.Join(dataDir, "events")
	events, err := store.New(storePath, filepath.Join(dataDir, "signatures.local"))
	if err != nil { return err }
	address := os.Getenv("BAV_EVENT_ADDR")
	if address == "" { address = "127.0.0.1:9777" }
	if err := requireLoopback(address); err != nil { return err }
	intake, err := server.New(server.Config{Address: address, Token: token, Store: events})
	if err != nil { return err }

	fmt.Printf("Beelzebub AV event bridge listening on %s\n", address)
	fmt.Printf("Event log directory: %s\n", storePath)
	fmt.Printf("Configure Beelzebub auth-token from: %s\n", tokenPath)
	fmt.Println("Raw credentials, cookies, headers, commands and request bodies are not persisted.")

	serverErrors := make(chan error, 1)
	go func() { serverErrors <- intake.ListenAndServe() }()
	signals := make(chan os.Signal, 1)
	signal.Notify(signals, os.Interrupt, syscall.SIGTERM)
	select {
	case signal := <-signals:
		fmt.Printf("Shutting down after %s\n", signal)
		return intake.Shutdown(5 * time.Second)
	case err := <-serverErrors:
		if errors.Is(err, net.ErrClosed) { return nil }
		return err
	}
}

func dataDirectory() (string, error) {
	if configured := strings.TrimSpace(os.Getenv("BAV_DATA_DIR")); configured != "" { return filepath.Abs(configured) }
	if runtime.GOOS == "windows" {
		base := os.Getenv("LOCALAPPDATA")
		if base == "" {
			home, err := os.UserHomeDir()
			if err != nil { return "", err }
			base = filepath.Join(home, "AppData", "Local")
		}
		return filepath.Join(base, "DuckOS", "BeelzebubAV"), nil
	}
	base := os.Getenv("XDG_DATA_HOME")
	if base == "" {
		home, err := os.UserHomeDir()
		if err != nil { return "", err }
		base = filepath.Join(home, ".local", "share")
	}
	return filepath.Join(base, "duckos", "beelzebub-av"), nil
}

func loadOrCreateToken(filename string) (string, string, error) {
	if supplied := os.Getenv("BAV_EVENT_TOKEN"); supplied != "" {
		if len(supplied) < 32 { return "", "", errors.New("BAV_EVENT_TOKEN must contain at least 32 characters") }
		return supplied, "environment variable BAV_EVENT_TOKEN", nil
	}
	if err := rejectExistingSymlink(filename); err != nil { return "", "", err }
	if data, err := os.ReadFile(filename); err == nil {
		token := strings.TrimSpace(string(data))
		if len(token) < 32 { return "", "", errors.New("existing ingest.token is invalid; remove it and restart to rotate") }
		return token, filename, nil
	} else if !os.IsNotExist(err) { return "", "", err }
	seed := make([]byte, 32)
	if _, err := rand.Read(seed); err != nil { return "", "", fmt.Errorf("generate BAV token: %w", err) }
	token := base64.RawURLEncoding.EncodeToString(seed)
	file, err := os.OpenFile(filename, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o600)
	if err != nil {
		if os.IsExist(err) { return loadOrCreateToken(filename) }
		return "", "", err
	}
	if _, err := file.WriteString(token + "\n"); err != nil { file.Close(); os.Remove(filename); return "", "", err }
	if err := file.Sync(); err != nil { file.Close(); os.Remove(filename); return "", "", err }
	if err := file.Close(); err != nil { return "", "", err }
	return token, filename, nil
}

func requireLoopback(address string) error {
	host, _, err := net.SplitHostPort(address)
	if err != nil { return fmt.Errorf("invalid BAV listen address: %w", err) }
	ip := net.ParseIP(host)
	if ip == nil || !ip.IsLoopback() { return errors.New("BAV event receiver may bind to loopback addresses only") }
	return nil
}
func rejectSymlink(path string) error {
	info, err := os.Lstat(path)
	if err != nil { return err }
	if info.Mode()&os.ModeSymlink != 0 || !info.IsDir() { return fmt.Errorf("path must be a real directory: %s", path) }
	return nil
}
func rejectExistingSymlink(path string) error {
	info, err := os.Lstat(path)
	if err != nil { if os.IsNotExist(err) { return nil }; return err }
	if info.Mode()&os.ModeSymlink != 0 || !info.Mode().IsRegular() { return fmt.Errorf("refusing non-regular file: %s", path) }
	return nil
}
