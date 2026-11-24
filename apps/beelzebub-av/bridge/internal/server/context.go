package server

import (
	"context"
	"time"
)

func contextWithTimeout(timeout time.Duration) (context.Context, context.CancelFunc) {
	if timeout <= 0 { timeout = 5 * time.Second }
	return context.WithTimeout(context.Background(), timeout)
}
