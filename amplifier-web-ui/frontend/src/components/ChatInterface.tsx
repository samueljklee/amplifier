import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

interface Props {
  executionId?: string
  events?: any[]
  onSendMessage?: (message: string) => void
}

export default function ChatInterface({ executionId, events, onSendMessage }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Convert interactive.prompt events into chat messages
  useEffect(() => {
    if (!events) return

    const messageMap = new Map<string, Message>()

    events.forEach((event: any, index: number) => {
      if (event.type === 'interactive.prompt') {
        const content = event.prompt_text || event.prompt || 'Please respond'
        const messageKey = `assistant-${content}`

        // Only add if we haven't seen this exact message
        if (!messageMap.has(messageKey)) {
          messageMap.set(messageKey, {
            id: `prompt-${index}-${event.timestamp || Date.now()}`,
            role: 'assistant',
            content,
            timestamp: new Date(event.timestamp || Date.now()),
          })
        }
      } else if (event.type === 'log' && event.message?.includes('✓ User response submitted:')) {
        // Extract user response from log
        const response = event.message.split('✓ User response submitted:')[1]?.trim()
        if (response) {
          const messageKey = `user-${response}`

          // Only add if we haven't seen this exact response
          if (!messageMap.has(messageKey)) {
            messageMap.set(messageKey, {
              id: `response-${index}-${event.timestamp || Date.now()}`,
              role: 'user',
              content: response,
              timestamp: new Date(event.timestamp || Date.now()),
            })
          }
        }
      }
    })

    // Convert Map to array, preserving insertion order
    const allMessages = Array.from(messageMap.values())
    setMessages(allMessages)
  }, [events])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !executionId) return

    setInput('')
    setIsLoading(true)

    if (onSendMessage) {
      onSendMessage(input)
    }

    // Send response to running scenario via /respond endpoint
    try {
      const res = await fetch(`/api/executions/${executionId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ response: input }),
      })

      if (!res.ok) {
        throw new Error('Failed to submit response')
      }
    } catch (error) {
      console.error('Failed to send input:', error)
      alert('Failed to send response. The scenario may have timed out or completed.')
    }

    setIsLoading(false)
  }

  return (
    <div className="flex flex-col max-h-[calc(100vh-16rem)] my-4 bg-white dark:bg-gray-800 rounded-lg shadow">
      {/* Chat Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {executionId ? 'Scenario Feedback' : 'Ultrathink Assistant'}
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {executionId
            ? 'Provide feedback and input to the running scenario'
            : 'Chat to create new scenarios or get help'}
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <p className="text-lg mb-2">👋 How can I help?</p>
            <p className="text-sm">
              {executionId
                ? 'Type your feedback when the scenario asks for input'
                : 'Describe what you want to create and I\'ll help build it'}
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : message.role === 'system'
                  ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-900 dark:text-yellow-200 border border-yellow-300 dark:border-yellow-700'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              <p className="text-xs opacity-70 mt-1">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}

        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="bg-gray-100 dark:bg-gray-700 rounded-lg px-4 py-2">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Thinking...</span>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={executionId ? "Type your feedback..." : "Describe what you want to create..."}
            className="flex-1 rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-4 py-2"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="bg-indigo-600 text-white px-6 py-2 rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            Send
          </button>
        </form>

        {!executionId && (
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setInput("Help me create a blog post summarizer")}
              className="text-xs px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              💡 Create blog summarizer
            </button>
            <button
              type="button"
              onClick={() => setInput("Build a meeting notes extractor")}
              className="text-xs px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              💡 Meeting notes tool
            </button>
            <button
              type="button"
              onClick={() => setInput("Help me analyze research papers")}
              className="text-xs px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              💡 Research analyzer
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
