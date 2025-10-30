import { useState } from 'react'
import TerminalProxy from './TerminalProxy'

export default function ToolGeneratorFlow() {
  const [executionId, setExecutionId] = useState<string | null>(null)
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [sentMessage, setSentMessage] = useState<string | null>(null)
  const [isWaiting, setIsWaiting] = useState(false)

  const handleSendMessage = async () => {
    if (!currentAnswer.trim()) return

    setIsWaiting(true)
    setSentMessage(currentAnswer) // Save the message before clearing
    const messageToSend = currentAnswer
    setCurrentAnswer('') // Clear input

    try {
      // Use Claude CLI endpoint (terminal mode only)
      const execId = crypto.randomUUID()
      const response = await fetch('/api/claude/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          execution_id: execId,
          prompt: messageToSend
        })
      })

      if (!response.ok) {
        throw new Error('Failed to start Claude CLI')
      }

      setExecutionId(execId)
    } catch (error) {
      console.error('Failed to start execution:', error)
      setIsWaiting(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Create New Tool</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Describe the tool you want to create and I'll help you build it
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500" />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Connected
          </span>
        </div>
      </div>

      {/* Input area - Always visible until execution starts */}
      {!isWaiting && (
        <div className="flex gap-2">
          <textarea
            value={currentAnswer}
            onChange={(e) => setCurrentAnswer(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSendMessage()
              }
            }}
            placeholder="Describe the tool you want to create... (e.g., 'Create a tool that analyzes code complexity' or paste your detailed requirements)"
            className="flex-1 p-4 border border-gray-300 dark:border-gray-600 rounded-lg resize-none focus:ring-2 focus:ring-indigo-500 dark:bg-gray-800 dark:text-white"
            rows={6}
            autoFocus
          />
          <button
            onClick={handleSendMessage}
            disabled={!currentAnswer.trim()}
            className="px-6 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      )}

      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
        {isWaiting
          ? 'Processing...'
          : 'Press Enter to send, Shift+Enter for new line'}
      </p>

      {/* Show sent message as chat bubble (matches original design) */}
      {sentMessage && (
        <div className="mt-6 flex justify-end">
          <div className="max-w-[80%] rounded-lg p-4 bg-indigo-600 text-white">
            <p className="whitespace-pre-wrap text-sm">{sentMessage}</p>
          </div>
        </div>
      )}

      {/* Terminal output */}
      {executionId && (
        <div className="mt-6 border-t border-gray-200 dark:border-gray-700 pt-4">
          <TerminalProxy executionId={executionId} />
        </div>
      )}
    </div>
  )
}