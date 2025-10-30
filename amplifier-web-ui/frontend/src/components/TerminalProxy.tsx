import { FitAddon } from '@xterm/addon-fit'
import { Terminal } from '@xterm/xterm'
import '@xterm/xterm/css/xterm.css'
import { useEffect, useRef } from 'react'

interface Props {
  executionId: string
}

export default function TerminalProxy({ executionId }: Props) {
  const terminalRef = useRef<HTMLDivElement>(null)
  const xtermRef = useRef<Terminal>()
  const wsRef = useRef<WebSocket>()

  // Detect if dark mode is active (at component level)
  const isDarkMode = document.documentElement.classList.contains('dark')

  useEffect(() => {
    if (!terminalRef.current) return

    // Theme colors matching browser theme
    const theme = isDarkMode ? {
      // Dark mode theme
      background: '#1e1e1e',
      foreground: '#d4d4d4',
      cursor: '#ffffff',
      black: '#000000',
      red: '#cd3131',
      green: '#0dbc79',
      yellow: '#e5e510',
      blue: '#2472c8',
      magenta: '#bc3fbc',
      cyan: '#11a8cd',
      white: '#e5e5e5',
      brightBlack: '#666666',
      brightRed: '#f14c4c',
      brightGreen: '#23d18b',
      brightYellow: '#f5f543',
      brightBlue: '#3b8eea',
      brightMagenta: '#d670d6',
      brightCyan: '#29b8db',
      brightWhite: '#ffffff',
    } : {
      // Light mode theme
      background: '#ffffff',
      foreground: '#1e1e1e',
      cursor: '#1e1e1e',
      black: '#000000',
      red: '#cd3131',
      green: '#0dbc79',
      yellow: '#e5e510',
      blue: '#2472c8',
      magenta: '#bc3fbc',
      cyan: '#11a8cd',
      white: '#e5e5e5',
      brightBlack: '#666666',
      brightRed: '#f14c4c',
      brightGreen: '#23d18b',
      brightYellow: '#f5f543',
      brightBlue: '#3b8eea',
      brightMagenta: '#d670d6',
      brightCyan: '#29b8db',
      brightWhite: '#1e1e1e',
    }

    // Create xterm instance with Canvas renderer for better compatibility
    const term = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Monaco, Menlo, "Courier New", monospace',
      theme,
      rows: 30,
      cols: 120,
      scrollback: 10000, // Large scrollback buffer to preserve history
      convertEol: true, // Convert \n to \r\n for proper line breaks
      allowTransparency: false,
      fastScrollModifier: 'shift', // Enable fast scrolling with shift
      rendererType: 'canvas', // Use Canvas renderer instead of DOM renderer
    })

    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)

    // Mount terminal
    term.open(terminalRef.current)
    console.log('Terminal opened, element:', terminalRef.current)
    console.log('Terminal rows:', term.rows, 'cols:', term.cols)

    // Test write to verify terminal is rendering
    term.write('🔵 Terminal initializing...\r\n')
    console.log('✅ Test write completed')

    // Fit after a short delay to ensure DOM is ready
    setTimeout(() => {
      fitAddon.fit()
      console.log('Terminal fitted. New size - rows:', term.rows, 'cols:', term.cols)
    }, 100)

    xtermRef.current = term

    // Connect WebSocket
    const wsUrl = `ws://localhost:8000/ws/claude/${executionId}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('Terminal proxy connected')

      // Send initial terminal size immediately
      ws.send(JSON.stringify({
        type: 'resize',
        rows: term.rows,
        cols: term.cols
      }))
    }

    ws.onmessage = (event) => {
      // PTY output → terminal
      if (event.data instanceof Blob) {
        event.data.arrayBuffer().then(buffer => {
          const bytes = new Uint8Array(buffer)
          const text = new TextDecoder().decode(bytes)

          // Write to terminal immediately (preserves ANSI control sequences)
          term.write(bytes)

          // Debug: Log what was written
          console.log('✍️ Wrote', bytes.length, 'bytes:', text.substring(0, 100))
        })
      } else if (typeof event.data === 'string') {
        // Handle JSON control messages
        try {
          const data = JSON.parse(event.data)
          console.log('Control message:', data)
        } catch (e) {
          console.log('Non-JSON text message:', event.data)
        }
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      term.writeln('\r\n\x1b[31m[Connection error]\x1b[0m\r\n')
    }

    ws.onclose = () => {
      console.log('Terminal proxy disconnected')
      term.writeln('\r\n\x1b[33m[Session ended]\x1b[0m\r\n')
    }

    // Handle user keyboard input → PTY
    term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(new TextEncoder().encode(data))
      }
    })

    // Handle window resize
    const handleResize = () => {
      fitAddon.fit()
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'resize',
          rows: term.rows,
          cols: term.cols
        }))
      }
    }

    window.addEventListener('resize', handleResize)

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize)
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
      term.dispose()
    }
  }, [executionId])

  return (
    <div className="mt-6 border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
      <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400 ml-2">Amplifier</span>
        </div>
        <span className="text-xs text-gray-500">Scroll up to see earlier output</span>
      </div>
      <div
        style={{
          width: '100%',
          height: '600px',
          padding: '8px',
          backgroundColor: isDarkMode ? '#1e1e1e' : '#ffffff',
          overflow: 'hidden'
        }}
      >
        <div
          ref={terminalRef}
          style={{
            width: '100%',
            height: '100%'
          }}
        />
      </div>
    </div>
  )
}
