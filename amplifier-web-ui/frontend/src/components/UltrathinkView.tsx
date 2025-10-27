import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

interface GenerationEvent {
  type: string
  data: any
  message?: string
  timestamp?: string
}

interface ConversationMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
}

export default function UltrathinkView() {
  const navigate = useNavigate()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [description, setDescription] = useState('')
  const [conversation, setConversation] = useState<ConversationMessage[]>([])
  const [currentMessage, setCurrentMessage] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [events, setEvents] = useState<GenerationEvent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isInstalling, setIsInstalling] = useState(false)
  const [installSuccess, setInstallSuccess] = useState(false)
  const [sessionStatus, setSessionStatus] = useState<string | null>(null)
  const [specJson, setSpecJson] = useState<any>(null)
  const logsEndRef = useRef<HTMLDivElement>(null)

  // Fetch session state periodically
  useEffect(() => {
    if (!sessionId) return

    const fetchState = async () => {
      try {
        const response = await fetch(`/api/ultrathink/sessions/${sessionId}`)
        if (response.ok) {
          const state = await response.json()
          setConversation(state.conversation || [])
          setSessionStatus(state.status)
          setSpecJson(state.spec_json)
        }
      } catch (err) {
        console.error('Error fetching session state:', err)
      }
    }

    fetchState()
    const interval = setInterval(fetchState, 1000)

    return () => clearInterval(interval)
  }, [sessionId])

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  // Connect to SSE stream when session is created
  useEffect(() => {
    if (!sessionId) return

    const eventSource = new EventSource(`http://localhost:8000/api/ultrathink/sessions/${sessionId}/events`)

    eventSource.onmessage = (e) => {
      const event = JSON.parse(e.data)
      setEvents(prev => [...prev, event])

      // If complete, stop generating
      if (event.type === 'complete') {
        setIsGenerating(false)
        eventSource.close()
      }

      // If error, show and stop
      if (event.type === 'error') {
        setError(event.data?.message || 'Generation failed')
        setIsGenerating(false)
        eventSource.close()
      }
    }

    eventSource.onerror = (err) => {
      console.error('SSE connection error', err)
      if (isComplete) {
        eventSource.close()
      }
    }

    return () => {
      eventSource.close()
    }
  }, [sessionId])

  const handleGenerate = async () => {
    if (!description.trim()) return

    setError(null)

    try {
      const response = await fetch('/api/ultrathink/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: description,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to create session')
      }

      const data = await response.json()
      setSessionId(data.session_id)
    } catch (err) {
      setError(String(err))
    }
  }

  const handleSendMessage = async () => {
    if (!currentMessage.trim() || !sessionId) return

    try {
      const response = await fetch(`/api/ultrathink/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: currentMessage,
          action: 'refine',
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      setCurrentMessage('')
    } catch (err) {
      setError(String(err))
    }
  }

  const handleApproveSpec = async () => {
    if (!sessionId) return

    setIsGenerating(true)

    try {
      const response = await fetch(`/api/ultrathink/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: 'Approved',
          action: 'generate',
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to approve spec')
      }
    } catch (err) {
      setError(String(err))
      setIsGenerating(false)
    }
  }

  const handleInstall = async () => {
    if (!sessionId) return

    setIsInstalling(true)
    setError(null)

    try {
      const response = await fetch(`/api/ultrathink/sessions/${sessionId}/install`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Installation failed')
      }

      setInstallSuccess(true)
    } catch (err) {
      setError(String(err))
    } finally {
      setIsInstalling(false)
    }
  }

  const isComplete = events.some(e => e.type === 'complete')
  const generatedScenarioId = events.find(e => e.type === 'complete')?.data?.scenario_id

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Create New Scenario
        </h2>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          {!sessionId ? "Describe what you want to build and we'll help you design it" : "Answer questions to refine your scenario"}
        </p>
      </div>

      {/* Input Form */}
      {!sessionId && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Describe Your Scenario
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Example: A tool that extracts action items from email threads. It should categorize tasks by priority and generate a structured todo list."
            className="w-full h-32 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-y"
          />
          <button
            onClick={handleGenerate}
            disabled={!description.trim()}
            className="mt-4 w-full bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-medium disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            ✨ Start Conversation
          </button>
        </div>
      )}

      {/* Conversation Interface */}
      {sessionId && sessionStatus === 'asking_questions' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            💬 Let's Design Your Scenario
          </h3>

          {/* Conversation History */}
          <div className="space-y-3 mb-4 max-h-96 overflow-y-auto">
            {conversation.map((msg, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg ${
                  msg.role === 'user'
                    ? 'bg-indigo-100 dark:bg-indigo-900/30 ml-8'
                    : msg.role === 'assistant'
                    ? 'bg-gray-100 dark:bg-gray-700 mr-8'
                    : 'bg-yellow-50 dark:bg-yellow-900/20 text-center text-sm'
                }`}
              >
                <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  {msg.role === 'user' ? 'You' : msg.role === 'assistant' ? '🤖 Assistant' : '📋 Context'}
                </div>
                <p className="text-gray-900 dark:text-white whitespace-pre-wrap">{msg.content}</p>
              </div>
            ))}
          </div>

          {/* Input Field */}
          <div className="flex gap-2">
            <input
              type="text"
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Type your answer..."
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            <button
              onClick={handleSendMessage}
              disabled={!currentMessage.trim()}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg font-medium disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      )}

      {/* Spec Review */}
      {sessionId && sessionStatus === 'spec_ready' && specJson && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            📋 Specification Ready for Review
          </h3>

          <div className="bg-gray-50 dark:bg-gray-900 rounded p-4 mb-4 max-h-96 overflow-y-auto">
            <pre className="text-sm text-gray-900 dark:text-white whitespace-pre-wrap">
              {JSON.stringify(specJson, null, 2)}
            </pre>
          </div>

          <button
            onClick={handleApproveSpec}
            disabled={isGenerating}
            className="w-full bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isGenerating ? '⚙️ Generating Code...' : '✅ Approve & Generate Code'}
          </button>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Progress Display */}
      {sessionId && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {isComplete ? '✅ Generation Complete' : '⏳ Generating...'}
            </h3>

            {/* Events List with improved formatting */}
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {events.map((event, idx) => {
                const isLog = event.type.startsWith('log.')
                const logLevel = isLog ? event.type.split('.')[1] : null

                // Determine styling based on event type
                let bgColor = 'bg-gray-50 dark:bg-gray-900'
                let icon = '📝'

                if (event.type === 'spec_ready') {
                  bgColor = 'bg-blue-50 dark:bg-blue-900/20'
                  icon = '✓'
                } else if (event.type === 'code.generating') {
                  bgColor = 'bg-purple-50 dark:bg-purple-900/20'
                  icon = '⚙️'
                } else if (event.type === 'code.generated') {
                  bgColor = 'bg-green-50 dark:bg-green-900/20'
                  icon = '✓'
                } else if (event.type === 'validation.started') {
                  bgColor = 'bg-yellow-50 dark:bg-yellow-900/20'
                  icon = '🔍'
                } else if (event.type === 'validation.passed') {
                  bgColor = 'bg-green-50 dark:bg-green-900/20'
                  icon = '✅'
                } else if (event.type === 'validation.failed') {
                  bgColor = 'bg-red-50 dark:bg-red-900/20'
                  icon = '❌'
                } else if (event.type === 'error') {
                  bgColor = 'bg-red-50 dark:bg-red-900/20'
                  icon = '❌'
                } else if (isLog) {
                  if (logLevel === 'error') {
                    bgColor = 'bg-red-50 dark:bg-red-900/20'
                    icon = '❌'
                  } else if (logLevel === 'warning' || logLevel === 'warn') {
                    bgColor = 'bg-yellow-50 dark:bg-yellow-900/20'
                    icon = '⚠️'
                  } else if (logLevel === 'info') {
                    icon = 'ℹ️'
                  } else if (logLevel === 'debug') {
                    icon = '🔧'
                  }
                }

                return (
                  <div
                    key={idx}
                    className={`flex items-start gap-3 p-3 ${bgColor} rounded transition-all hover:shadow-sm`}
                  >
                    <span className="text-lg flex-shrink-0">{icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 dark:text-white break-words">
                        {event.message || event.data?.message || event.type}
                      </p>
                      {event.data?.file && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 font-mono">
                          {event.data.file}
                        </p>
                      )}
                      {event.data?.context && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {event.data.context}
                        </p>
                      )}
                      {/* Show timestamp for log entries */}
                      {isLog && event.timestamp && (
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {new Date(event.timestamp).toLocaleTimeString()}
                        </p>
                      )}
                    </div>
                  </div>
                )
              })}
              {/* Auto-scroll target */}
              <div ref={logsEndRef} />
            </div>

            {/* Session Info */}
            {sessionId && (
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Session ID: <code className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">{sessionId}</code>
                </p>
              </div>
            )}
          </div>

          {/* Completion Actions */}
          {isComplete && generatedScenarioId && (
            <div className="bg-green-50 dark:bg-green-900/20 border-2 border-green-500 dark:border-green-400 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-3xl">🎉</span>
                <h3 className="text-xl font-bold text-green-900 dark:text-green-100">
                  Scenario Generated Successfully!
                </h3>
              </div>
              <p className="text-green-800 dark:text-green-200 mb-4">
                Your new scenario "{generatedScenarioId}" is ready to use.
              </p>

              {/* Installation Status */}
              {installSuccess ? (
                <div className="mb-4 p-3 bg-green-100 dark:bg-green-900/40 border border-green-300 dark:border-green-700 rounded-lg">
                  <p className="text-green-900 dark:text-green-100 font-medium">
                    ✓ Scenario installed to scenarios/{generatedScenarioId}/
                  </p>
                </div>
              ) : (
                <button
                  onClick={handleInstall}
                  disabled={isInstalling}
                  className="w-full mb-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-lg font-medium disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {isInstalling ? '📦 Installing...' : '📦 Install Scenario'}
                </button>
              )}

              <div className="flex gap-3">
                <button
                  onClick={() => navigate('/')}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  ← Back to Scenarios
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  ✨ Create Another
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
