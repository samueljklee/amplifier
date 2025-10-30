import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useWebSocket } from '../hooks/useWebSocket'
import type { AgentCompleteEvent, AgentStartEvent, InteractivePromptEvent, LogEvent, ProgressEvent, StageTransitionEvent, StreamOutputEvent } from '../types/api'
import TerminalProxy from './TerminalProxy'

interface Message {
  role: 'assistant' | 'user' | 'status' | 'streaming'
  content: string
  timestamp: Date
  source?: 'assistant' | 'tool' | 'thinking' | 'agent'
}

interface Props {
  executionId: string | null
  onComplete: () => void
  onStartExecution: (initialMessage: string) => Promise<void>
}

// Removed predefined suggestions - users now describe their tool directly

export default function ConversationPhase({ executionId, onComplete, onStartExecution }: Props) {
  const [searchParams] = useSearchParams()
  const useTerminal = !searchParams.has('customCreateScenario')

  // Don't connect to regular WebSocket in terminal mode (terminal has its own WS connection)
  const { events, isConnected } = useWebSocket(useTerminal ? '' : (executionId || ''))
  const [messages, setMessages] = useState<Message[]>([])
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [isWaiting, setIsWaiting] = useState(false)
  const [hasNewMessages, setHasNewMessages] = useState(false)
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true)
  const [logsExpanded, setLogsExpanded] = useState(true)
  const [expandedMessages, setExpandedMessages] = useState<Set<number>>(new Set())

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const logsContainerRef = useRef<HTMLDivElement>(null)

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

  // Listen for streaming output and accumulate
  useEffect(() => {
    const streamEvents = events.filter(
      (e): e is StreamOutputEvent => e.type === 'stream.output'
    )

    if (streamEvents.length > 0) {
      // Group consecutive stream events by source to create message chunks
      const latestEvent = streamEvents[streamEvents.length - 1]

      setMessages(prev => {
        // Check if last message is a streaming message with same source
        const lastMsg = prev[prev.length - 1]
        if (lastMsg && lastMsg.role === 'streaming' && lastMsg.source === latestEvent.source) {
          // Append to existing streaming message
          return [
            ...prev.slice(0, -1),
            {
              ...lastMsg,
              content: lastMsg.content + latestEvent.text,
              timestamp: new Date(latestEvent.timestamp || Date.now())
            }
          ]
        } else {
          // Create new streaming message
          return [...prev, {
            role: 'streaming' as const,
            content: latestEvent.text,
            source: latestEvent.source,
            timestamp: new Date(latestEvent.timestamp || Date.now())
          }]
        }
      })
    }
  }, [events])

  // Listen for meaningful status updates and add them to conversation
  useEffect(() => {
    events.forEach((e) => {
      let statusContent: string | null = null

      if (e.type === 'progress') {
        const progressEvent = e as ProgressEvent
        statusContent = progressEvent.message
      } else if (e.type === 'agent.start') {
        const agentEvent = e as AgentStartEvent
        statusContent = `🤖 ${agentEvent.message}`
      } else if (e.type === 'agent.complete') {
        const agentEvent = e as AgentCompleteEvent
        statusContent = `✅ ${agentEvent.message}`
      } else if (e.type === 'stage.transition') {
        const stageEvent = e as StageTransitionEvent
        if (stageEvent.to_stage) {
          statusContent = `📍 Starting ${stageEvent.to_stage} stage...`
        }
      }

      if (statusContent) {
        // Check if this status message already exists
        const alreadyExists = messages.some(
          msg => msg.role === 'status' && msg.content === statusContent
        )

        if (!alreadyExists) {
          setMessages(prev => [...prev, {
            role: 'status',
            content: statusContent,
            timestamp: new Date(e.timestamp || Date.now())
          }])
        }
      }
    })
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

  // Check if logs container is near bottom
  const isLogsNearBottom = (container: HTMLElement) => {
    const threshold = 50 // pixels from bottom
    const position = container.scrollHeight - container.scrollTop - container.clientHeight
    return position < threshold
  }

  // Auto-scroll logs when new events arrive (only if user is already at bottom)
  useEffect(() => {
    if (!logsExpanded || events.length === 0) return

    const container = logsContainerRef.current
    if (!container) return

    // Only auto-scroll if user is near the bottom
    if (isLogsNearBottom(container)) {
      // Use setTimeout to ensure the DOM has updated with new events
      setTimeout(() => {
        container.scrollTop = container.scrollHeight
      }, 0)
    }
  }, [events.length, logsExpanded])

  const handleSendMessage = async () => {
    if (!currentAnswer.trim()) return

    const messageContent = currentAnswer
    setMessages(prev => [...prev, {
      role: 'user',
      content: messageContent,
      timestamp: new Date()
    }])

    // Enable auto-scroll when user sends a message
    setShouldAutoScroll(true)
    setIsWaiting(true)
    setCurrentAnswer('')

    // Start execution if not started yet, or send response if already running
    try {
      if (!executionId) {
        await onStartExecution(messageContent)
      } else {
        await fetch(`/api/executions/${executionId}/respond`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ response: messageContent })
        })
      }
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

      {/* Conversation history */}
      {messages.length > 0 && (
        <div className="relative mb-6">
          <div
            ref={scrollContainerRef}
            onScroll={handleScroll}
            className="space-y-4 max-h-[500px] overflow-y-auto"
          >
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${msg.role === 'user'
                    ? 'bg-indigo-600 text-white'
                    : msg.role === 'status'
                      ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-blue-900 dark:text-blue-200'
                      : msg.role === 'streaming'
                        ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-900 dark:text-green-200'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                    }`}
                >
                  {msg.role === 'streaming' && msg.source && (
                    <div className="text-xs font-semibold mb-2 flex items-center gap-1">
                      <span className="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                      {msg.source}
                    </div>
                  )}
                  <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                  <span className="text-xs opacity-70 mt-2 block">
                    {msg.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}

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
      )}

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
            rows={messages.length === 0 ? 6 : 3}
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

      {/* Execution output section - Terminal or Logs */}
      {executionId && (
        <div className="mt-6 border-t border-gray-200 dark:border-gray-700 pt-4">
          {useTerminal ? (
            // Terminal mode - PTY output in xterm.js
            <TerminalProxy executionId={executionId} />
          ) : (
            // Log mode - Parsed event logs (current implementation)
            events.length > 0 && (
              <>
                <button
                  onClick={() => setLogsExpanded(!logsExpanded)}
                  className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 transition-colors"
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${logsExpanded ? 'rotate-90' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <span>Execution Logs ({events.length} events)</span>
                </button>

                {logsExpanded && (
                  <div
                    ref={logsContainerRef}
                    className="mt-3 bg-gray-50 dark:bg-gray-800 rounded-lg p-4 max-h-80 overflow-y-auto font-mono text-xs"
                  >
                    {/* Deduplicate: Prefer stream.output over log events with similar content */}
                    {(() => {
                      const seen = new Set<string>()

                      // Normalize content by removing common prefixes for comparison
                      const normalizeContent = (text: string): string => {
                        return text
                          .trim()
                          .replace(/^\[amplifier\]\s*/i, '')
                          .replace(/^\[assistant\]\s*/i, '')
                          .replace(/^\[agent\]\s*/i, '')
                          .replace(/^\[tool\]\s*/i, '')
                          .trim()
                      }

                      const dedupedEvents = events.filter((event) => {
                        if (event.type === 'stream.output') {
                          const streamEvent = event as StreamOutputEvent
                          const normalized = normalizeContent(streamEvent.text)
                          seen.add(normalized)
                          return true // Always show stream.output
                        } else if (event.type === 'log') {
                          const logEvent = event as LogEvent
                          const normalized = normalizeContent(logEvent.message || '')
                          // Skip log events if we've seen similar content in stream.output
                          if (seen.has(normalized)) {
                            return false
                          }
                          return true
                        }
                        return true // Show all other event types
                      })

                      return dedupedEvents.map((event, i) => (
                        <div key={i} className="mb-1 text-gray-700 dark:text-gray-300">
                          <span className="text-gray-500 dark:text-gray-500">
                            [{new Date(event.timestamp || Date.now()).toLocaleTimeString()}]
                          </span>{' '}
                          <span className="text-blue-600 dark:text-blue-400">[{event.type}]</span>{' '}
                          {event.type === 'log' && (event as LogEvent).message}
                          {event.type === 'progress' && (event as ProgressEvent).message}
                          {event.type === 'agent.start' && `Agent: ${(event as AgentStartEvent).agent}`}
                          {event.type === 'agent.complete' && `Agent complete: ${(event as AgentCompleteEvent).agent}`}
                          {event.type === 'stage.transition' &&
                            `Stage: ${(event as StageTransitionEvent).from_stage || 'start'} → ${(event as StageTransitionEvent).to_stage}`}
                          {event.type === 'stream.output' && (() => {
                            const streamEvent = event as StreamOutputEvent
                            const colorClass =
                              streamEvent.source === 'agent' ? 'text-purple-600 dark:text-purple-400' :
                                streamEvent.source === 'tool' ? 'text-amber-600 dark:text-amber-400' :
                                  streamEvent.source === 'thinking' ? 'text-gray-500 dark:text-gray-400 italic' :
                                    'text-green-600 dark:text-green-400' // assistant (default)

                            const isLongMessage = streamEvent.text.length > 300
                            const isExpanded = expandedMessages.has(i)
                            const displayText = isLongMessage && !isExpanded
                              ? streamEvent.text.substring(0, 300) + '...'
                              : streamEvent.text

                            return (
                              <span className={colorClass}>
                                [{streamEvent.source}] {displayText}
                                {isLongMessage && (
                                  <button
                                    onClick={() => {
                                      const newExpanded = new Set(expandedMessages)
                                      if (isExpanded) {
                                        newExpanded.delete(i)
                                      } else {
                                        newExpanded.add(i)
                                      }
                                      setExpandedMessages(newExpanded)
                                    }}
                                    className="ml-2 text-blue-500 dark:text-blue-400 hover:underline text-xs"
                                  >
                                    {isExpanded ? 'Show less' : 'Show more'}
                                  </button>
                                )}
                              </span>
                            )
                          })()}
                        </div>
                      ))
                    })()}
                  </div>
                )}
              </>
            )
          )}
        </div>
      )}
    </div>
  )
}
