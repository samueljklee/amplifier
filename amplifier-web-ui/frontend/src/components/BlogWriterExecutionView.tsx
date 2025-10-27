import { useParams } from 'react-router-dom'
import { useState, useEffect, useMemo } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import WorkflowViz from './WorkflowViz'
import LogStream from './LogStream'
import DraftViewer from './DraftViewer'
import ApprovalControls from './ApprovalControls'
import IterationTimeline from './IterationTimeline'
import { WritingIcon, CheckIcon, CelebrationIcon, LibraryIcon } from './Icons'

interface FileCreatedEvent {
  type: 'file.created'
  path: string
  metadata?: {
    type?: string
    title?: string
    word_count?: number
    iteration?: number
  }
}

interface InteractivePromptEvent {
  type: 'interactive.prompt'
  prompt: string
  metadata?: {
    iteration?: number
    prompt_type?: string
  }
}

interface ReviewResultEvent {
  type: 'log'
  message: string
  metadata?: {
    review_type?: 'source' | 'style'
    needs_revision?: boolean
    issues?: Array<{
      type: string
      description: string
      severity?: 'low' | 'medium' | 'high'
    }>
    summary?: string
  }
}

interface IterationEntry {
  iteration: number
  type: 'draft' | 'revision' | 'user_feedback' | 'review'
  timestamp?: string
  metadata?: {
    word_count?: number
    action?: string
    issue_count?: number
  }
}

interface ReviewResult {
  needs_revision: boolean
  issues: Array<{
    type: string
    description: string
    severity?: 'low' | 'medium' | 'high'
  }>
  summary?: string
}

export default function BlogWriterExecutionView() {
  const { executionId } = useParams<{ executionId: string }>()
  const { events, isConnected } = useWebSocket(executionId || null)
  const [isProcessingAction, setIsProcessingAction] = useState(false)
  const [selectedIteration, setSelectedIteration] = useState<number | null>(null)
  const [lastPromptIteration, setLastPromptIteration] = useState<number | null>(null)

  if (!executionId) {
    return <div>Invalid execution ID</div>
  }

  const blogWriterData = useMemo(() => {
    let currentIteration = 1
    const drafts: Array<{ iteration: number; path: string; wordCount?: number }> = []
    const iterations: IterationEntry[] = []
    let sourceReview: ReviewResult | null = null
    let styleReview: ReviewResult | null = null
    let activePrompt: InteractivePromptEvent | null = null

    events.forEach((event: any) => {
      if (event.type === 'file.created' && event.metadata?.type === 'draft') {
        const fileEvent = event as FileCreatedEvent
        const iteration = fileEvent.metadata?.iteration || currentIteration
        drafts.push({
          iteration,
          path: fileEvent.path,
          wordCount: fileEvent.metadata?.word_count,
        })

        iterations.push({
          iteration,
          type: 'draft',
          timestamp: event.timestamp,
          metadata: {
            word_count: fileEvent.metadata?.word_count,
          },
        })

        currentIteration = Math.max(currentIteration, iteration)
      }

      // Also capture final output file (non-draft file.created events)
      if (event.type === 'file.created' && !event.metadata?.type) {
        // This is the final output file
        const fileEvent = event as FileCreatedEvent
        drafts.push({
          iteration: currentIteration + 1, // Final is after last iteration
          path: fileEvent.path,
          wordCount: fileEvent.metadata?.word_count,
        })
      }

      if (event.type === 'log' && event.metadata?.review_type) {
        const reviewEvent = event as ReviewResultEvent
        const reviewType = reviewEvent.metadata?.review_type

        const reviewResult: ReviewResult = {
          needs_revision: reviewEvent.metadata?.needs_revision || false,
          issues: reviewEvent.metadata?.issues || [],
          summary: reviewEvent.metadata?.summary,
        }

        if (reviewType === 'source') {
          sourceReview = reviewResult
        } else if (reviewType === 'style') {
          styleReview = reviewResult
        }

        if (reviewEvent.metadata?.needs_revision) {
          iterations.push({
            iteration: currentIteration,
            type: 'review',
            timestamp: event.timestamp,
            metadata: {
              issue_count: reviewEvent.metadata?.issues?.length || 0,
            },
          })
        }
      }

      if (event.type === 'interactive.prompt') {
        activePrompt = event as InteractivePromptEvent
        const iteration = event.metadata?.iteration || currentIteration
        currentIteration = Math.max(currentIteration, iteration)
      }

      // Clear active prompt when execution completes
      if (event.type === 'execution.complete') {
        activePrompt = null
      }

      if (event.type === 'log' && event.message?.includes('Iteration ')) {
        const match = event.message.match(/Iteration (\d+)/)
        if (match) {
          const iteration = parseInt(match[1], 10)
          currentIteration = Math.max(currentIteration, iteration)
        }
      }
    })

    // Sort drafts by iteration for proper ordering
    const sortedDrafts = drafts.sort((a, b) => a.iteration - b.iteration)
    const currentDraft = sortedDrafts.length > 0 ? sortedDrafts[sortedDrafts.length - 1] : null

    return {
      currentIteration,
      currentDraft,
      drafts: sortedDrafts,
      iterations: iterations.sort((a, b) => a.iteration - b.iteration),
      sourceReview,
      styleReview,
      activePrompt,
    }
  }, [events])

  // Determine which draft to display based on selection or default to latest
  const displayDraft = selectedIteration !== null
    ? blogWriterData.drafts.find(d => d.iteration === selectedIteration) || blogWriterData.currentDraft
    : blogWriterData.currentDraft

  // Reset processing state when a new prompt arrives
  useEffect(() => {
    if (blogWriterData.activePrompt) {
      const promptIteration = blogWriterData.currentIteration
      if (lastPromptIteration !== promptIteration) {
        setLastPromptIteration(promptIteration)
        setIsProcessingAction(false) // New prompt arrived, ready for user input
      }
    }
  }, [blogWriterData.activePrompt, blogWriterData.currentIteration, lastPromptIteration])

  const isComplete = events.some((e) => e.type === 'execution.complete')

  // Also check if blog_writer specifically completed (it saves final output)
  const hasFinalOutput = events.some((e: any) =>
    e.type === 'log' && (
      e.message?.includes('Blog post saved to:') ||
      e.message?.includes('✅ Blog post saved')
    )
  )

  const handleApprove = async () => {
    console.log('Approval action: approve', { executionId, iteration: blogWriterData.currentIteration })
    setIsProcessingAction(true)

    try {
      const response = await fetch(`/api/executions/${executionId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ response: 'approve' }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Failed to send approval:', errorText)
        throw new Error(errorText)
      }

      // Keep processing state true - controls will stay hidden until completion
    } catch (error) {
      console.error('Error sending approval:', error)
      setIsProcessingAction(false)
    }
  }

  const handleRevise = async (comments?: string) => {
    console.log('Approval action: revise', {
      executionId,
      iteration: blogWriterData.currentIteration,
      comments
    })
    setIsProcessingAction(true)

    try {
      const response = await fetch(`/api/executions/${executionId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          response: 'revise',
          comments: comments || undefined,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Failed to send revision request:', errorText)
        setIsProcessingAction(false)
        throw new Error(errorText)
      }

      // Keep processing state true - controls will stay hidden until next prompt arrives
    } catch (error) {
      console.error('Error sending revision request:', error)
      setIsProcessingAction(false)
    }
  }

  const handleSkip = async () => {
    console.log('Approval action: skip', { executionId, iteration: blogWriterData.currentIteration })
    setIsProcessingAction(true)

    try {
      const response = await fetch(`/api/executions/${executionId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ response: 'skip' }),
      })

      if (!response.ok) {
        console.error('Failed to send skip:', await response.text())
        setIsProcessingAction(false)
      }

      // Keep processing state true - controls will stay hidden until next prompt arrives
    } catch (error) {
      console.error('Error sending skip:', error)
      setIsProcessingAction(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            {isComplete ? (
              <>
                <CheckIcon size={28} className="text-green-600" />
                <span>Blog Post Complete</span>
              </>
            ) : (
              <>
                <WritingIcon size={28} className="text-indigo-600" />
                <span>Blog Writer in Progress</span>
              </>
            )}
          </h2>
          <div className="flex items-center gap-2">
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {displayDraft && (
            <div className="space-y-4">
              {/* Draft Navigation - show if there are multiple drafts */}
              {blogWriterData.drafts.length > 1 && (
                <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4 border border-indigo-200 dark:border-indigo-800">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-indigo-900 dark:text-indigo-100 flex items-center gap-2">
                      <LibraryIcon size={18} className="text-indigo-600 dark:text-indigo-400" />
                      Version History ({blogWriterData.drafts.length} drafts)
                    </span>
                    {selectedIteration !== null && (
                      <button
                        onClick={() => setSelectedIteration(null)}
                        className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
                      >
                        ← Back to latest
                      </button>
                    )}
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {blogWriterData.drafts.map((draft, idx) => {
                      const isLast = idx === blogWriterData.drafts.length - 1
                      const isFinal = isLast && (isComplete || hasFinalOutput)

                      return (
                        <button
                          key={draft.iteration}
                          onClick={() => setSelectedIteration(draft.iteration)}
                          className={`px-3 py-1.5 rounded text-sm font-medium transition-all flex items-center gap-1.5 ${
                            (selectedIteration || blogWriterData.currentIteration) === draft.iteration
                              ? isFinal
                                ? 'bg-green-600 text-white shadow'
                                : 'bg-indigo-600 text-white shadow'
                              : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/40'
                          }`}
                        >
                          {isFinal ? (
                            <>
                              <CheckIcon size={14} className="text-white" />
                              Final
                            </>
                          ) : (
                            `v${draft.iteration}`
                          )}
                          {!isFinal && draft.iteration === blogWriterData.currentIteration && ' (Latest)'}
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}

              <DraftViewer
                draftPath={displayDraft.path}
                iteration={displayDraft.iteration}
                wordCount={displayDraft.wordCount}
              />
            </div>
          )}

          {/* Show approval controls only if not complete, there's an active prompt, AND not processing */}
          {!isComplete && !hasFinalOutput && blogWriterData.activePrompt && !isProcessingAction && (
            <ApprovalControls
              onApprove={handleApprove}
              onRevise={handleRevise}
              onSkip={handleSkip}
              isProcessing={isProcessingAction}
              iteration={blogWriterData.currentIteration}
            />
          )}

          {/* Show processing message while waiting for response */}
          {isProcessingAction && !isComplete && !hasFinalOutput && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-blue-900 dark:text-blue-100 font-medium">
                  Processing your response...
                </span>
              </div>
            </div>
          )}

          {/* Show completion message when done */}
          {(isComplete || hasFinalOutput) && (
            <div className="bg-green-50 dark:bg-green-900/20 border-2 border-green-500 dark:border-green-400 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-3">
                <CelebrationIcon size={32} className="text-green-600 dark:text-green-400" />
                <h3 className="text-xl font-bold text-green-900 dark:text-green-100">
                  Blog Post Complete!
                </h3>
              </div>
              <p className="text-green-800 dark:text-green-200 text-sm">
                Your blog post has been successfully generated and saved. You can view all versions using the version history above.
              </p>
            </div>
          )}

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Execution Logs
            </h3>
            <LogStream events={events} />
          </div>
        </div>

        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 sticky top-6">
            <IterationTimeline
              iterations={blogWriterData.iterations}
              currentIteration={selectedIteration || blogWriterData.currentIteration}
              onSelectIteration={setSelectedIteration}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
