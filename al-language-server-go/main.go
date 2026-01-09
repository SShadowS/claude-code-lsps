package main

import (
	"fmt"
	"os"

	"github.com/SShadowS/claude-code-lsps/al-language-server-go/wrapper"
)

func main() {
	w := wrapper.New()

	if err := w.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "AL LSP Wrapper error: %v\n", err)
		os.Exit(1)
	}
}
