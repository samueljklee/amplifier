import { useState, useEffect, useRef } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import { AnalyzerIcon, DocumentIcon, SearchIcon, MagicIcon, IdeaIcon } from './Icons'
import type { InteractivePromptEvent, StageTransitionEvent } from '../types/api'

interface Message {
  role: 'assistant' | 'user'
  content: string
  timestamp: Date
}

interface Props {
  executionId: string
  onComplete: () => void
}

const SUGGESTIONS = [
  {
    icon: <AnalyzerIcon />,
    label: 'Code Analyzer',
    description: 'Analyze code complexity and quality metrics',
    fullText: 'Create a tool that analyzes code complexity, calculates metrics like cyclomatic complexity, and identifies potential issues.'
  },
  {
    icon: <DocumentIcon />,
    label: 'Document Converter',
    description: 'Convert between different file formats',
    fullText: 'Build a tool that converts documents between formats like CSV to JSON, Markdown to HTML, with validation and error handling.'
  },
  {
    icon: <SearchIcon />,
    label: 'Text Processor',
    description: 'Extract and analyze text from files',
    fullText: 'Make a tool that processes text files to extract key information, summarize content, or perform analysis like sentiment or keyword extraction.'
  },
  {
    icon: <MagicIcon />,
    label: 'Custom Tool',
    description: 'Start from scratch',
    fullText: ''
  }
]

export default function ConversationPhase({ executionId, onComplete }: Props) {
  const { events, isConnected } = useWebSocket(executionId)
  const [messages, setMessages] = useState<Message[]>([])
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [isWaiting, setIsWaiting] = useState(true)
  const [showSuggestions, setShowSuggestions] = useState(true)
  const [conversationStarted, setConversationStarted] = useState(false)
  const [hasNewMessages, setHasNewMessages] = useState(false)
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  // Listen for interactive.prompt events
  useEffect(() => {
    const promptEvents = events.filter(
      (e): e is InteractivePromptEvent => e.type === 'interactive.prompt'
    )

    if (promptEvents.length > 0) {
      setIsWaiting(false)

      // Only process new prompt events that haven't been added yet
      const latestPrompt = promptEvents[promptEvents.length - 1]
      const latestPromptText = latestPrompt.prompt_text

      // Check if this message already exists
      const alreadyExists = messages.some(
        msg => msg.role === 'assistant' && msg.content === latestPromptText
      )

      if (!alreadyExists) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: latestPromptText,
          timestamp: new Date(latestPrompt.timestamp || Date.now())
        }])
      }
    }
  }, [events, messages])

  // Detect when conversation is complete (generation stage starts)
  useEffect(() => {
    const hasGenerationStage = events.some((e): e is StageTransitionEvent =>
      e.type === 'stage.transition' && e.to_stage === 'generation'
    )

    if (hasGenerationStage && !isWaiting) {
      onComplete()
    }
  }, [events, isWaiting, onComplete])

  // Check if user is near bottom of scroll container
  const isNearBottom = () => {
    const container = scrollContainerRef.current
    if (!container) return true

    const threshold = 100 // pixels from bottom
    const position = container.scrollHeight - container.scrollTop - container.clientHeight
    return position < threshold
  }

  // Handle scroll events to detect if user scrolled away
  const handleScroll = () => {
    if (isNearBottom()) {
      setShouldAutoScroll(true)
      setHasNewMessages(false)
    } else {
      setShouldAutoScroll(false)
    }
  }

  // Auto-scroll when new messages arrive (if user is near bottom)
  useEffect(() => {
    if (messages.length === 0) return

    if (shouldAutoScroll) {
      // User is near bottom, auto-scroll to new message
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    } else {
      // User is scrolled up, show notification
      setHasNewMessages(true)
    }
  }, [messages, shouldAutoScroll])

  // When user sends a message, enable auto-scroll
  const scrollToBottom = () => {
    setShouldAutoScroll(true)
    setHasNewMessages(false)
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSuggestionClick = async (suggestion: typeof SUGGESTIONS[0]) => {
    // Mark conversation as started and hide suggestions
    setConversationStarted(true)
    setShowSuggestions(false)

    if (!suggestion.fullText) {
      // Custom tool - just enable input for user to type
      return
    }

    // Auto-inject the suggestion as user's answer
    setMessages(prev => [...prev, {
      role: 'user',
      content: suggestion.fullText,
      timestamp: new Date()
    }])

    // Enable auto-scroll when user sends a message
    setShouldAutoScroll(true)
    setIsWaiting(true)

    // Send to backend
    try {
      await fetch(`/api/executions/${executionId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ response: suggestion.fullText })
      })
    } catch (error) {
      console.error('Failed to send response:', error)
      setIsWaiting(false)
    }
  }

  const handleManualAnswer = async () => {
    if (!currentAnswer.trim()) return

    // Mark conversation as started and hide suggestions
    setConversationStarted(true)
    setShowSuggestions(false)

    setMessages(prev => [...prev, {
      role: 'user',
      content: currentAnswer,
      timestamp: new Date()
    }])

    // Enable auto-scroll when user sends a message
    setShouldAutoScroll(true)
    setIsWaiting(true)

    try {
      await fetch(`/api/executions/${executionId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ response: currentAnswer })
      })
    } catch (error) {
      console.error('Failed to send response:', error)
      setIsWaiting(false)
    }

    setCurrentAnswer('')
  }

  return (
    <div className="max-w-3xl mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Create New Tool</h1>
        <div className="flex items-center gap-2">
          <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-yellow-500'}`} />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {isConnected ? 'Connected' : 'Connecting...'}
          </span>
        </div>
      </div>

      {/* Suggestion Pills - Show until user starts conversation */}
      {showSuggestions && !conversationStarted && (
        <div className="mb-6 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg p-6">
          <p className="text-sm text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <IdeaIcon size={18} />
            Choose a starting point:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {SUGGESTIONS.map((suggestion, i) => (
              <button
                key={i}
                onClick={() => handleSuggestionClick(suggestion)}
                className="text-left p-4 bg-white dark:bg-gray-800 rounded-lg border-2 border-transparent hover:border-indigo-400 dark:hover:border-indigo-600 transition-all group"
              >
                <div className="flex items-start gap-3">
                  {suggestion.icon}
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                      {suggestion.label}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {suggestion.description}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Conversation history - Only show after user takes action */}
      {conversationStarted && (
        <>
          <div className="relative">
            <div
              ref={scrollContainerRef}
              onScroll={handleScroll}
              className="space-y-4 mb-6 max-h-[500px] overflow-y-auto"
            >
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-4 ${msg.role === 'user'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                      }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    <span className="text-xs opacity-70 mt-2 block">
                      {msg.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}

              {isWaiting && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                      <div className="animate-pulse">●</div>
                      <div className="animate-pulse" style={{ animationDelay: '0.2s' }}>●</div>
                      <div className="animate-pulse" style={{ animationDelay: '0.4s' }}>●</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Invisible anchor for scrolling */}
              <div ref={messagesEndRef} />
            </div>

            {/* Floating "New messages" button */}
            {hasNewMessages && (
              <button
                onClick={scrollToBottom}
                className="absolute bottom-2 left-1/2 transform -translate-x-1/2 px-4 py-2 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 transition-all flex items-center gap-2 animate-bounce"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
                New messages
              </button>
            )}
          </div>

          {/* Input area - Show after conversation starts */}
          {!isWaiting && (
            <div className="flex gap-2">
              <textarea
                value={currentAnswer}
                onChange={(e) => setCurrentAnswer(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleManualAnswer()
                  }
                }}
                placeholder="Type your answer..."
                className="flex-1 p-4 border border-gray-300 dark:border-gray-600 rounded-lg resize-none focus:ring-2 focus:ring-indigo-500 dark:bg-gray-800 dark:text-white"
                rows={3}
                autoFocus
              />
              <button
                onClick={handleManualAnswer}
                disabled={!currentAnswer.trim()}
                className="px-6 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:cursor-not-allowed transition-colors"
              >
                Send
              </button>
            </div>
          )}

          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            {isWaiting
              ? 'Waiting for response...'
              : 'Press Enter to send, Shift+Enter for new line'}
          </p>
        </>
      )}
    </div>
  )
}