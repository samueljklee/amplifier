import { useState } from 'react'

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

interface Props {
  iterations: IterationEntry[]
  currentIteration: number
  onSelectIteration?: (iteration: number) => void
}

const EVENT_ICONS: Record<string, string> = {
  draft: '📝',
  revision: '✏️',
  user_feedback: '👤',
  review: '🔍',
  style: '🎨',
}

const ACTION_LABELS: Record<string, string> = {
  approve: 'Approved',
  revise: 'Requested revision',
  skip: 'Skipped',
}

export default function IterationTimeline({
  iterations,
  currentIteration,
  onSelectIteration
}: Props) {
  const [collapsed, setCollapsed] = useState(false)

  const shouldCollapse = iterations.length > 5
  const displayIterations = collapsed ? iterations.slice(-3) : iterations

  const getWordCountChange = (iteration: number) => {
    if (iteration === 1) return null
    const current = iterations.find(i => i.iteration === iteration)
    const previous = iterations.find(i => i.iteration === iteration - 1)

    if (!current?.metadata?.word_count || !previous?.metadata?.word_count) return null

    const diff = current.metadata.word_count - previous.metadata.word_count
    if (diff === 0) return null
    return diff > 0 ? `+${diff}` : `${diff}`
  }

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const getIterationLabel = (entry: IterationEntry) => {
    if (entry.type === 'draft' && entry.iteration === 1) return 'Initial Draft'
    if (entry.type === 'revision') return 'Revision'
    return entry.type.charAt(0).toUpperCase() + entry.type.slice(1)
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
          Timeline
        </h3>
        {shouldCollapse && (
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            {collapsed ? 'Show all' : 'Collapse'}
          </button>
        )}
      </div>

      <div className="relative">
        {collapsed && shouldCollapse && (
          <div className="flex items-center gap-2 mb-2 text-xs text-gray-500">
            <div className="w-px h-4 bg-gray-300 dark:bg-gray-600 ml-2" />
            <span>... {iterations.length - 3} older iterations</span>
          </div>
        )}

        <div className="space-y-3">
          {displayIterations.map((entry, index) => {
            const isLast = index === displayIterations.length - 1
            const isCurrent = entry.iteration === currentIteration
            const isClickable = onSelectIteration && entry.iteration !== currentIteration
            const wordCountDiff = getWordCountChange(entry.iteration)

            return (
              <div key={`${entry.iteration}-${entry.type}-${index}`} className="relative">
                {!isLast && (
                  <div className="absolute left-2 top-8 bottom-0 w-px bg-gray-300 dark:bg-gray-600 -mb-3" />
                )}

                <button
                  onClick={() => isClickable && onSelectIteration(entry.iteration)}
                  disabled={!isClickable}
                  className={`
                    relative w-full text-left rounded-lg p-3 transition-all
                    ${isCurrent
                      ? 'bg-indigo-50 dark:bg-indigo-900/20 border-2 border-indigo-500 dark:border-indigo-400'
                      : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
                    }
                    ${isClickable
                      ? 'hover:shadow-md cursor-pointer hover:border-indigo-300 dark:hover:border-indigo-600'
                      : 'cursor-default'
                    }
                  `}
                >
                  <div className="flex items-start gap-3">
                    <div className={`
                      flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs
                      ${isCurrent
                        ? 'bg-indigo-500 text-white ring-4 ring-indigo-100 dark:ring-indigo-900/30'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                      }
                    `}>
                      {entry.iteration}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm">
                          {EVENT_ICONS[entry.type]}
                        </span>
                        <span className={`text-sm font-medium ${
                          isCurrent
                            ? 'text-indigo-900 dark:text-indigo-100'
                            : 'text-gray-900 dark:text-white'
                        }`}>
                          {getIterationLabel(entry)}
                        </span>
                        {isCurrent && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500 text-white">
                            Current
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
                        {entry.metadata?.word_count && (
                          <span>
                            {entry.metadata.word_count.toLocaleString()} words
                          </span>
                        )}
                        {wordCountDiff && (
                          <span className={
                            wordCountDiff.startsWith('+')
                              ? 'text-green-600 dark:text-green-400'
                              : 'text-red-600 dark:text-red-400'
                          }>
                            ({wordCountDiff})
                          </span>
                        )}
                        {entry.timestamp && (
                          <span className="text-gray-500">
                            {formatTimestamp(entry.timestamp)}
                          </span>
                        )}
                      </div>

                      {entry.metadata?.action && (
                        <div className="mt-2 flex items-center gap-1 text-xs">
                          <span>👤</span>
                          <span className="text-gray-700 dark:text-gray-300">
                            User: {ACTION_LABELS[entry.metadata.action] || entry.metadata.action}
                          </span>
                        </div>
                      )}

                      {entry.metadata?.issue_count !== undefined && (
                        <div className="mt-2 text-xs">
                          <span className={
                            entry.metadata.issue_count === 0
                              ? 'text-green-600 dark:text-green-400'
                              : 'text-amber-600 dark:text-amber-400'
                          }>
                            {entry.metadata.issue_count === 0
                              ? '✓ No issues'
                              : `⚠ ${entry.metadata.issue_count} issue${entry.metadata.issue_count > 1 ? 's' : ''}`
                            }
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              </div>
            )
          })}

          {iterations.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No iterations yet
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
