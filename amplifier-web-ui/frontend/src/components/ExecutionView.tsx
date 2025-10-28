import { useParams } from 'react-router-dom'
import { useState, useEffect, useMemo } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import WorkflowViz from './WorkflowViz'
import LogStream from './LogStream'
import ChatInterface from './ChatInterface'
import InteractivePrompt from './InteractivePrompt'
import { simpleMarkdownToHtml } from '../utils/markdown'
import { FilePreviewIcon, ReviewIcon, EditIcon, AnalyzerIcon, DocumentIcon } from './Icons'

interface FileContent {
  path: string
  content: string
  filename: string
}

export default function ExecutionView() {
  const { executionId } = useParams<{ executionId: string }>()
  const { events, isConnected } = useWebSocket(executionId || null)
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<FileContent | null>(null)
  const [loadingFile, setLoadingFile] = useState(false)
  const [viewMode, setViewMode] = useState<'raw' | 'preview'>('preview')
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false)

  if (!executionId) {
    return <div>Invalid execution ID</div>
  }

  // Check if execution is complete
  const isComplete = events.some(
    (e) => e.type === 'execution.complete'
  )

  // Detect active interactive prompt
  const activePrompt = useMemo(() => {
    const promptEvents = events.filter((e: any) => e.type === 'interactive.prompt')
    if (promptEvents.length === 0) return null

    const latestPrompt = promptEvents[promptEvents.length - 1]

    // Check if already responded to this specific prompt
    // Look for response submission AFTER this prompt's timestamp
    const responded = events.some((e: any) =>
      e.timestamp && latestPrompt.timestamp &&
      e.timestamp > latestPrompt.timestamp &&
      e.type === 'log' &&
      (e.message?.includes('✓ Received answer') || e.message?.includes('✓ User response submitted'))
    )

    // Simple: if responded, hide the prompt (will reappear if new prompt arrives)
    return responded ? null : latestPrompt
  }, [events])

  // Check if scenario needs input (fallback for old-style prompts)
  const needsInput = events.some(
    (e: any) => e.type === 'log' && e.message?.toLowerCase().includes('feedback')
  )

  // Extract output information from logs and structured events
  const outputFiles: Array<{path: string, metadata?: any}> = []
  const outputDir = events.find(
    (e: any) => e.type === 'log' && e.message?.includes('Output directory:')
  )?.message?.split('Output directory:')[1]?.trim()

  events.forEach((e: any) => {
    // Check for structured file.created events first
    if (e.type === 'file.created') {
      outputFiles.push({
        path: e.path,
        metadata: e.metadata
      })
    }
    // Fall back to parsing log messages
    else if (e.type === 'log' && e.message?.includes('Successfully saved to:')) {
      const filePath = e.message.split('Successfully saved to:')[1]?.trim()
      if (filePath) outputFiles.push({path: filePath})
    }
  })

  // Fetch file content when a file is selected
  useEffect(() => {
    if (selectedFile) {
      setLoadingFile(true)
      fetch(`/api/files/read?path=${encodeURIComponent(selectedFile)}`)
        .then(res => res.json())
        .then(data => {
          setFileContent(data)
          setLoadingFile(false)
        })
        .catch(err => {
          console.error('Error loading file:', err)
          setLoadingFile(false)
        })
    } else {
      setFileContent(null)
    }
  }, [selectedFile])

  // Debug: Count event types
  const eventCounts = events.reduce((acc, e) => {
    acc[e.type] = (acc[e.type] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Main execution view - 2 columns on large screens */}
      <div className="lg:col-span-2 space-y-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              {isComplete ? 'Execution Complete' : 'Execution in Progress'}
            </h2>
            <div className="flex items-center gap-2">
              {/* Debug: Show event types */}
              <div className="text-xs text-gray-500 dark:text-gray-400 mr-4">
                Events: {Object.entries(eventCounts).map(([type, count]) => `${type}:${count}`).join(', ')}
              </div>
              <div
                className={`h-3 w-3 rounded-full ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>

          <WorkflowViz events={events} />
        </div>

        {/* Output Files Section */}
        {outputFiles.length > 0 && (
          <div className={`border rounded-lg shadow p-6 ${
            isComplete
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
              : 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
          }`}>
            <h3 className={`text-lg font-semibold mb-4 flex items-center gap-2 ${
              isComplete
                ? 'text-green-900 dark:text-green-100'
                : 'text-blue-900 dark:text-blue-100'
            }`}>
              {isComplete ? (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                </svg>
              )}
              {isComplete ? 'Generated Files' : 'Draft Files'}
            </h3>
            {outputDir && (
              <p className="text-sm text-green-700 dark:text-green-300 mb-3 flex items-center gap-2">
                <DocumentIcon size={16} /> Output directory: <code className="bg-green-100 dark:bg-green-900/40 px-2 py-1 rounded">{outputDir}</code>
              </p>
            )}
            <div className="space-y-2">
              {outputFiles.map((file, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedFile(file.path === selectedFile ? null : file.path)}
                  className={`w-full text-left p-3 rounded transition-colors ${
                    selectedFile === file.path
                      ? 'bg-green-200 dark:bg-green-800'
                      : 'hover:bg-green-100 dark:hover:bg-green-900/40'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <FilePreviewIcon size={16} className="text-green-700 dark:text-green-300" />
                    <code className="flex-1 text-sm text-green-900 dark:text-green-100">
                      {file.path.split('/').pop()}
                    </code>
                    {selectedFile === file.path && <ReviewIcon size={16} className="text-green-700 dark:text-green-300" />}
                  </div>
                  {file.metadata && (
                    <div className="mt-2 flex gap-4 text-xs text-green-700 dark:text-green-300 ml-6">
                      {file.metadata.title && (
                        <span className="flex items-center gap-1">
                          <EditIcon size={12} /> {file.metadata.title}
                        </span>
                      )}
                      {file.metadata.word_count && (
                        <span className="flex items-center gap-1">
                          <AnalyzerIcon size={12} /> {file.metadata.word_count} words
                        </span>
                      )}
                      {file.metadata.image_count !== undefined && (
                        <span className="flex items-center gap-1">
                          <FilePreviewIcon size={12} /> {file.metadata.image_count} images
                        </span>
                      )}
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* File Preview Section */}
        {selectedFile && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <FilePreviewIcon size={20} /> {fileContent?.filename || 'Loading...'}
              </h3>
              <div className="flex items-center gap-2">
                {/* View Mode Toggle */}
                <div className="flex bg-gray-200 dark:bg-gray-700 rounded-md p-1">
                  <button
                    onClick={() => setViewMode('preview')}
                    className={`px-3 py-1 text-sm rounded transition-colors ${
                      viewMode === 'preview'
                        ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    Preview
                  </button>
                  <button
                    onClick={() => setViewMode('raw')}
                    className={`px-3 py-1 text-sm rounded transition-colors ${
                      viewMode === 'raw'
                        ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    Raw
                  </button>
                </div>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 ml-2"
                >
                  ✕
                </button>
              </div>
            </div>

            {loadingFile ? (
              <div className="flex items-center justify-center py-12 text-gray-500 dark:text-gray-400">
                Loading file content...
              </div>
            ) : fileContent ? (
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 overflow-auto max-h-[600px]">
                {viewMode === 'raw' ? (
                  <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono leading-relaxed">
                    {fileContent.content}
                  </pre>
                ) : (
                  <div
                    className="max-w-none"
                    dangerouslySetInnerHTML={{ __html: simpleMarkdownToHtml(fileContent.content) }}
                  />
                )}
              </div>
            ) : (
              <div className="text-gray-500 dark:text-gray-400 text-center py-12">
                Failed to load file content
              </div>
            )}
          </div>
        )}

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Execution Logs
          </h3>
          <LogStream events={events} />
        </div>
      </div>

      {/* Chat sidebar - 1 column on large screens */}
      <div className="lg:col-span-1">
        <div className="sticky top-6">
          {(needsInput || activePrompt) && (
            <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                💬 Scenario is waiting for your input
              </p>
            </div>
          )}

          {/* Show InteractivePrompt when there's an active prompt, otherwise show ChatInterface */}
          {activePrompt ? (
            <InteractivePrompt
              prompt={(activePrompt as any).prompt_text || (activePrompt as any).prompt || 'Please respond'}
              promptType={(activePrompt as any).prompt_type || 'text'}
              options={(activePrompt as any).prompt_options}
              onSubmit={async (response) => {
                setIsWaitingForResponse(true)
                try {
                  await fetch(`/api/executions/${executionId}/respond`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ response })
                  })
                } catch (error) {
                  console.error('Failed to submit response:', error)
                  alert('Failed to submit. Please try again.')
                } finally {
                  setIsWaitingForResponse(false)
                }
              }}
              isLoading={isWaitingForResponse}
              metadata={{
                iteration: (activePrompt as any).metadata?.iteration,
                helpText: "Provide your response to continue"
              }}
            />
          ) : (
            <ChatInterface executionId={executionId} events={events} />
          )}
        </div>
      </div>
    </div>
  )
}
