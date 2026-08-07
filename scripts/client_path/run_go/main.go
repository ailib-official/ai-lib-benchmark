// Client-path latency runner (ai-lib-go Client.Chat → mock). GOV-007 Bench B.
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/ailib-official/ai-lib-go/pkg/ailib"
)

func main() {
	mockURL := strings.TrimRight(envOr("MOCK_HTTP_URL", "http://127.0.0.1:4010"), "/")
	samples := 5
	if v := os.Getenv("SAMPLES"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			samples = n
		}
	}

	c, err := ailib.NewClientBuilder().
		WithBaseURL(mockURL).
		WithAPIKey("sk-test").
		WithTimeout(15 * time.Second).
		WithMaxRetries(0).
		Build()
	if err != nil {
		fatal(err)
	}
	defer c.Close()

	lat := make([]float64, 0, samples)
	errors := 0
	for i := 0; i < samples; i++ {
		t0 := time.Now()
		resp, err := c.Chat(context.Background(), []ailib.Message{
			{Role: ailib.RoleUser, Content: "Hello"},
		}, &ailib.ChatOptions{Model: "gpt-4o"})
		ms := float64(time.Since(t0).Milliseconds())
		lat = append(lat, ms)
		if err != nil {
			errors++
			fmt.Fprintf(os.Stderr, "error: %v\n", err)
			continue
		}
		if len(resp.Choices) == 0 {
			errors++
		}
	}

	mean, minV, maxV := stats(lat)
	out := map[string]any{
		"harness":  "client-path-mock",
		"runtime":  "ai-lib-go",
		"path":     "Client.Chat",
		"mock_url": mockURL,
		"model":    "gpt-4o",
		"samples":  samples,
		"ok":       samples - errors,
		"errors":   errors,
		"latency_ms": map[string]any{
			"mean": round2(mean),
			"min":  round2(minV),
			"max":  round2(maxV),
		},
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	_ = enc.Encode(out)
	if errors > 0 {
		os.Exit(1)
	}
}

func envOr(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

func stats(xs []float64) (mean, minV, maxV float64) {
	minV, maxV = xs[0], xs[0]
	sum := 0.0
	for _, x := range xs {
		sum += x
		if x < minV {
			minV = x
		}
		if x > maxV {
			maxV = x
		}
	}
	return sum / float64(len(xs)), minV, maxV
}

func round2(v float64) float64 {
	return float64(int(v*100+0.5)) / 100
}

func fatal(err error) {
	fmt.Fprintf(os.Stderr, "fatal: %v\n", err)
	os.Exit(2)
}
