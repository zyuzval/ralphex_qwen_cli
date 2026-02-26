// Package executor provides CLI execution for Claude, Codex, and Qwen tools.
package executor

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"strings"
)

// QwenExecutor runs qwen CLI commands with streaming JSON parsing.
type QwenExecutor struct {
	Command       string            // command to execute, defaults to "qwen"
	Args          string            // additional arguments (space-separated), defaults to standard args
	OutputHandler func(text string) // called for each text chunk, can be nil
	Debug         bool              // enable debug output
	ErrorPatterns []string          // patterns to detect in output (e.g., rate limit messages)
	cmdRunner     CommandRunner     // for testing, nil uses default
}

// Run executes qwen CLI with the given prompt and parses streaming JSON output.
func (e *QwenExecutor) Run(ctx context.Context, prompt string) Result {
	cmd := e.Command
	if cmd == "" {
		cmd = "qwen"
	}

	// build args from configured string or use defaults
	var args []string
	if e.Args != "" {
		args = splitArgs(e.Args)
	} else {
		args = []string{
			"--yolo", // equivalent to --dangerously-skip-permissions in Claude
			"--output-format", "stream-json",
		}
	}
	args = append(args, "--prompt", prompt)

	runner := e.cmdRunner
	if runner == nil {
		runner = &execClaudeRunner{} // reuse the same runner as Claude
	}

	stdout, wait, err := runner.Run(ctx, cmd, args...)
	if err != nil {
		return Result{Error: err}
	}

	result := e.parseStream(ctx, stdout)

	if err := wait(); err != nil {
		// check if it was context cancellation
		if ctx.Err() != nil {
			return Result{Output: result.Output, Signal: result.Signal, Error: ctx.Err()}
		}
		// non-zero exit might still have useful output
		if result.Output == "" {
			return Result{Error: fmt.Errorf("qwen exited with error: %w", err)}
		}
	}

	// check for error patterns in output
	if pattern := checkErrorPatterns(result.Output, e.ErrorPatterns); pattern != "" {
		return Result{
			Output: result.Output,
			Signal: result.Signal,
			Error:  &PatternMatchError{Pattern: pattern, HelpCmd: "qwen --help"},
		}
	}

	return result
}

// parseStream reads and parses the JSON stream from qwen CLI.
// checks ctx.Done() on each iteration so cancellation is not blocked by slow pipe reads.
func (e *QwenExecutor) parseStream(ctx context.Context, r io.Reader) Result {
	var output strings.Builder
	var signal string

	scanner := bufio.NewScanner(r)
	// increase buffer size for large JSON lines (large diffs with parallel agents)
	buf := make([]byte, 0, 64*1024)
	scanner.Buffer(buf, MaxScannerBuffer)

	for scanner.Scan() {
		select {
		case <-ctx.Done():
			return Result{Output: output.String(), Signal: signal, Error: fmt.Errorf("stream read: %w", ctx.Err())}
		default:
		}
		line := scanner.Text()
		if line == "" {
			continue
		}

		var event streamEvent
		if err := json.Unmarshal([]byte(line), &event); err != nil {
			// print non-JSON lines as-is
			if e.Debug {
				fmt.Printf("[debug] non-JSON line: %s\n", line)
			}
			output.WriteString(line)
			output.WriteString("\n")
			if e.OutputHandler != nil {
				e.OutputHandler(line + "\n")
			}
			continue
		}

		text := e.extractText(&event)
		if text != "" {
			// check for signals in text first
			if sig := detectSignal(text); sig != "" {
				signal = sig
				// If the entire text is a signal, don't add it to output
				// If text contains a signal among other content, strip the signal part
				signalPos := strings.Index(text, sig)
				if signalPos == 0 && len(text) == len(sig) {
					// Entire text is just the signal, don't add to output
				} else if signalPos >= 0 {
					// Text contains signal, add parts before and after signal
					prefix := text[:signalPos]
					suffix := text[signalPos+len(sig):]
					cleanText := prefix + suffix
					if cleanText != "" {
						output.WriteString(cleanText)
						if e.OutputHandler != nil {
							e.OutputHandler(cleanText)
						}
					}
				} else {
					// No signal found in text despite detectSignal returning one
					output.WriteString(text)
					if e.OutputHandler != nil {
						e.OutputHandler(text)
					}
				}
			} else {
				// No signal, add text as-is
				output.WriteString(text)
				if e.OutputHandler != nil {
					e.OutputHandler(text)
				}
			}
		}
	}

	if err := scanner.Err(); err != nil {
		return Result{Output: output.String(), Signal: signal, Error: fmt.Errorf("stream read: %w", err)}
	}

	return Result{Output: output.String(), Signal: signal}
}

// extractText extracts text content from various event types.
// This is the same as ClaudeExecutor's extractText method
func (e *QwenExecutor) extractText(event *streamEvent) string {
	switch event.Type {
	case "assistant":
		// assistant events contain message.content array with text blocks
		var texts []string
		for _, c := range event.Message.Content {
			if c.Type == "text" && c.Text != "" {
				texts = append(texts, c.Text)
			}
		}
		return strings.Join(texts, "")
	case "content_block_delta":
		if event.Delta.Type == "text_delta" {
			return event.Delta.Text
		}
	case "message_stop":
		// check final message content
		for _, c := range event.Message.Content {
			if c.Type == "text" {
				return c.Text
			}
		}
	case "result":
		// result can be a string or object with "output" field
		if len(event.Result) == 0 {
			return ""
		}
		
		// First, try to unmarshal as an object with output field
		var resultObj struct {
			Output string `json:"output"`
		}
		if err := json.Unmarshal(event.Result, &resultObj); err == nil {
			return resultObj.Output
		}
		
		// If that fails, it might be a JSON string containing the object
		// Try to unmarshal as a string first
		var resultStr string
		if err := json.Unmarshal(event.Result, &resultStr); err == nil {
			// If it's a string that looks like JSON, try to parse it as an object
			var nestedResultObj struct {
				Output string `json:"output"`
			}
			if err := json.Unmarshal([]byte(resultStr), &nestedResultObj); err == nil {
				return nestedResultObj.Output
			}
			// Otherwise return the string as-is (might contain signals)
			return resultStr
		}
	}
	return ""
}