package executor

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/umputun/ralphex/pkg/executor/mocks"
)

func TestQwenExecutor_Run(t *testing.T) {
	t.Run("successful execution with completion signal", func(t *testing.T) {
		ctrl := &mocks.CommandRunnerMock{}
		var capturedOutput string
		outputHandler := func(text string) {
			capturedOutput += text
		}

		// Create JSON stream output that includes a completion signal
		streamData := `{"type":"assistant","message":{"content":[{"type":"text","text":"Processing your request..."}]}}
{"type":"result","result":"{\"output\":\"<<<RALPHEX:ALL_TASKS_DONE>>>\"}"}
`

		ctrl.RunFunc = func(ctx context.Context, name string, args ...string) (io.Reader, func() error, error) {
			return strings.NewReader(streamData), func() error { return nil }, nil
		}

		executor := &QwenExecutor{
			Command:       "qwen",
			Args:          "--yolo --output-format stream-json",
			OutputHandler: outputHandler,
			cmdRunner:     ctrl,
		}

		result := executor.Run(context.Background(), "test prompt")

		assert.NoError(t, result.Error)
		assert.Equal(t, "<<<RALPHEX:ALL_TASKS_DONE>>>", result.Signal)
		assert.Contains(t, capturedOutput, "Processing your request...")
	})

	t.Run("execution with error", func(t *testing.T) {
		ctrl := &mocks.CommandRunnerMock{}
		ctrl.RunFunc = func(ctx context.Context, name string, args ...string) (io.Reader, func() error, error) {
			return nil, nil, errors.New("command failed")
		}

		executor := &QwenExecutor{
			Command:   "qwen",
			cmdRunner: ctrl,
		}

		result := executor.Run(context.Background(), "test prompt")

		assert.Error(t, result.Error)
		assert.Contains(t, result.Error.Error(), "command failed")
	})

	t.Run("execution with context cancellation", func(t *testing.T) {
		ctrl := &mocks.CommandRunnerMock{}
		
		// Create a cancelled context to simulate cancellation during execution
		ctx, cancel := context.WithCancel(context.Background())
		cancel() // Cancel immediately

		streamData := `{"type":"assistant","message":{"content":[{"type":"text","text":"Processing..."}]}}`

		ctrl.RunFunc = func(ctx context.Context, name string, args ...string) (io.Reader, func() error, error) {
			return strings.NewReader(streamData), func() error { return nil }, nil
		}

		executor := &QwenExecutor{
			Command:   "qwen",
			cmdRunner: ctrl,
		}

		result := executor.Run(ctx, "test prompt")

		assert.Error(t, result.Error)
		assert.True(t, errors.Is(result.Error, context.Canceled))
	})

	t.Run("execution with error patterns", func(t *testing.T) {
		ctrl := &mocks.CommandRunnerMock{}
		streamData := `{"type":"assistant","message":{"content":[{"type":"text","text":"You've hit your limit"}]}}`

		ctrl.RunFunc = func(ctx context.Context, name string, args ...string) (io.Reader, func() error, error) {
			return strings.NewReader(streamData), func() error { return nil }, nil
		}

		executor := &QwenExecutor{
			Command:       "qwen",
			ErrorPatterns: []string{"You've hit your limit"},
			cmdRunner:     ctrl,
		}

		result := executor.Run(context.Background(), "test prompt")

		assert.Error(t, result.Error)
		assert.Contains(t, result.Error.Error(), "detected error pattern")
	})
}

func TestQwenExecutor_parseStream(t *testing.T) {
	t.Run("parses assistant events correctly", func(t *testing.T) {
		streamData := `{"type":"assistant","message":{"content":[{"type":"text","text":"Hello world"}]}}
{"type":"content_block_delta","delta":{"type":"text_delta","text":"more text"}}
{"type":"result","result":"{\"output\":\"<<<RALPHEX:ALL_TASKS_DONE>>>\"}"}
`

		executor := &QwenExecutor{}
		result := executor.parseStream(context.Background(), strings.NewReader(streamData))

		assert.Equal(t, "Hello worldmore text", result.Output)
		assert.Equal(t, "<<<RALPHEX:ALL_TASKS_DONE>>>", result.Signal)
	})

	t.Run("handles non-JSON lines gracefully", func(t *testing.T) {
		streamData := `non-json line
{"type":"assistant","message":{"content":[{"type":"text","text":"Valid JSON"}]}}
another non-json line
`
		
		executor := &QwenExecutor{}
		result := executor.parseStream(context.Background(), strings.NewReader(streamData))

		assert.Contains(t, result.Output, "non-json line")
		assert.Contains(t, result.Output, "Valid JSON")
		assert.Contains(t, result.Output, "another non-json line")
		assert.Empty(t, result.Signal)
	})

	t.Run("handles message_stop events", func(t *testing.T) {
		streamData := `{"type":"message_stop","message":{"content":[{"type":"text","text":"Final message"}]}}
`
		
		executor := &QwenExecutor{}
		result := executor.parseStream(context.Background(), strings.NewReader(streamData))

		assert.Contains(t, result.Output, "Final message")
	})

	t.Run("context cancellation during parsing", func(t *testing.T) {
		ctx, cancel := context.WithCancel(context.Background())
		cancel() // Cancel immediately
		
		executor := &QwenExecutor{}
		result := executor.parseStream(ctx, strings.NewReader("test"))

		assert.Error(t, result.Error)
		assert.True(t, errors.Is(result.Error, context.Canceled))
	})
}

func TestQwenExecutor_extractText(t *testing.T) {
	executor := &QwenExecutor{}

	t.Run("extracts text from assistant event", func(t *testing.T) {
		event := streamEvent{
			Type: "assistant",
			Message: struct {
				Content []struct {
					Type string `json:"type"`
					Text string `json:"text"`
				} `json:"content"`
			}{
				Content: []struct {
					Type string `json:"type"`
					Text string `json:"text"`
				}{
					{Type: "text", Text: "Hello"},
					{Type: "text", Text: " World"},
				},
			},
		}

		result := executor.extractText(&event)
		assert.Equal(t, "Hello World", result)
	})

	t.Run("extracts text from content_block_delta", func(t *testing.T) {
		event := streamEvent{
			Type: "content_block_delta",
			Delta: struct {
				Type string `json:"type"`
				Text string `json:"text"`
			}{
				Type: "text_delta",
				Text: "delta text",
			},
		}

		result := executor.extractText(&event)
		assert.Equal(t, "delta text", result)
	})

	t.Run("extracts text from message_stop", func(t *testing.T) {
		event := streamEvent{
			Type: "message_stop",
			Message: struct {
				Content []struct {
					Type string `json:"type"`
					Text string `json:"text"`
				} `json:"content"`
			}{
				Content: []struct {
					Type string `json:"type"`
					Text string `json:"text"`
				}{
					{Type: "text", Text: "stop message"},
				},
			},
		}

		result := executor.extractText(&event)
		assert.Equal(t, "stop message", result)
	})

	t.Run("extracts text from result object", func(t *testing.T) {
		resultObj := struct {
			Output string `json:"output"`
		}{
			Output: "result output",
		}
		jsonBytes, _ := json.Marshal(resultObj)

		event := streamEvent{
			Type:    "result",
			Result:  json.RawMessage(jsonBytes),
		}

		result := executor.extractText(&event)
		assert.Equal(t, "result output", result)
	})

	t.Run("returns empty for unsupported event types", func(t *testing.T) {
		event := streamEvent{Type: "unsupported"}

		result := executor.extractText(&event)
		assert.Equal(t, "", result)
	})
}

func TestQwenExecutor_Run_DefaultCommand(t *testing.T) {
	ctrl := &mocks.CommandRunnerMock{}
	streamData := `{"type":"assistant","message":{"content":[{"type":"text","text":"Default command test"}]}}
{"type":"result","result":"{\"output\":\"<<<RALPHEX:ALL_TASKS_DONE>>>\"}"}
`

	ctrl.RunFunc = func(ctx context.Context, name string, args ...string) (io.Reader, func() error, error) {
		return strings.NewReader(streamData), func() error { return nil }, nil
	}

	executor := &QwenExecutor{
		OutputHandler: func(text string) {},
		cmdRunner:     ctrl,
	}

	result := executor.Run(context.Background(), "test prompt")

	assert.NoError(t, result.Error)
	assert.Equal(t, "<<<RALPHEX:ALL_TASKS_DONE>>>", result.Signal)
}