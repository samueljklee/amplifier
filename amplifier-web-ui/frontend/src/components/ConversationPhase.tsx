import { useState } from 'react'
import TerminalProxy from './TerminalProxy'

interface Props {
  executionId: string | null
  onStartExecution: (initialMessage: string) => Promise<void>
}

export default function ConversationPhase({ executionId, onStartExecution }: Props) {
  // Terminal mode only - no WebSocket for standard execution
  const isConnected = true // Always show connected in terminal mode
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [isWaiting, setIsWaiting] = useState(false)

  const handleSendMessage = async () => {
    if (!currentAnswer.trim()) return

    setIsWaiting(true)
    setCurrentAnswer('')

    // Start execution - terminal mode only
    try {
      await onStartExecution(currentAnswer)
    } catch (error) {
      console.error('Failed to send response:', error)
      setIsWaiting(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Create New Scenario</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Describe the scenario you want to create and I'll help you build it
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-yellow-500'}`} />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {isConnected ? 'Connected' : 'Connecting...'}
          </span>
        </div>
      </div>

      {/* Input area - Always visible at bottom */}
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

      {/* Terminal output */}
      {executionId && (
        <div className="mt-6 border-t border-gray-200 dark:border-gray-700 pt-4">
          <TerminalProxy executionId={executionId} />
        </div>
      )}
    </div>
  )
}
