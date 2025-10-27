import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface ReviewIssue {
  type: string
  description: string
  severity?: 'low' | 'medium' | 'high'
}

interface ReviewResult {
  needs_revision: boolean
  issues: ReviewIssue[]
  summary?: string
}

interface Props {
  sourceReview: ReviewResult | null
  styleReview: ReviewResult | null
}

const severityConfig = {
  low: {
    color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300',
    icon: 'ℹ️',
  },
  medium: {
    color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
    icon: '⚠️',
  },
  high: {
    color: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
    icon: '🚨',
  },
}

function ReviewSection({
  title,
  icon,
  review,
  defaultExpanded = false,
}: {
  title: string
  icon: string
  review: ReviewResult | null
  defaultExpanded?: boolean
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  if (!review) {
    return (
      <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-6">
        <div className="flex items-center gap-2 text-gray-400 dark:text-gray-500">
          <span className="text-2xl">{icon}</span>
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
        <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
          Reviews will appear here
        </p>
      </div>
    )
  }

  const hasIssues = review.needs_revision && review.issues.length > 0
  const bgColor = hasIssues
    ? 'bg-yellow-50 dark:bg-yellow-900/20'
    : 'bg-green-50 dark:bg-green-900/20'
  const borderColor = hasIssues
    ? 'border-yellow-300 dark:border-yellow-600'
    : 'border-green-300 dark:border-green-600'

  return (
    <div className={`${bgColor} border ${borderColor} rounded-lg overflow-hidden`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-6 text-left hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{icon}</span>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {title}
              </h3>
              <div className="flex items-center gap-2 mt-1">
                {hasIssues ? (
                  <>
                    <span className="text-xl">⚠️</span>
                    <span className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
                      {review.issues.length} issue{review.issues.length !== 1 ? 's' : ''} found
                    </span>
                  </>
                ) : (
                  <>
                    <span className="text-xl">✓</span>
                    <span className="text-sm font-medium text-green-800 dark:text-green-300">
                      No issues found
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className="text-gray-400"
          >
            ▼
          </motion.div>
        </div>

        {review.summary && !isExpanded && (
          <p className="mt-3 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
            {review.summary}
          </p>
        )}
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6 border-t border-gray-200 dark:border-gray-700 pt-4">
              {review.summary && (
                <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
                  {review.summary}
                </p>
              )}

              {hasIssues ? (
                <div className="space-y-3">
                  {review.issues.map((issue, index) => {
                    const severity = issue.severity || 'low'
                    const config = severityConfig[severity]

                    return (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm"
                      >
                        <div className="flex items-start gap-3">
                          <span className="text-lg">{config.icon}</span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {issue.type}
                              </span>
                              <span
                                className={`px-2 py-0.5 text-xs rounded-full ${config.color}`}
                              >
                                {severity}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {issue.description}
                            </p>
                          </div>
                        </div>
                      </motion.div>
                    )
                  })}
                </div>
              ) : (
                <div className="flex items-center gap-2 text-green-700 dark:text-green-300">
                  <span className="text-xl">🎉</span>
                  <p className="text-sm">All checks passed successfully!</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function ReviewFeedbackPanel({ sourceReview, styleReview }: Props) {
  const hasAnyReview = sourceReview !== null || styleReview !== null

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-6">
        <span className="text-2xl">📋</span>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Review Feedback</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ReviewSection
          title="Source Review"
          icon="🔍"
          review={sourceReview}
          defaultExpanded={sourceReview?.needs_revision}
        />
        <ReviewSection
          title="Style Review"
          icon="🎨"
          review={styleReview}
          defaultExpanded={styleReview?.needs_revision}
        />
      </div>

      {!hasAnyReview && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <p className="text-lg mb-2">No reviews available yet</p>
          <p className="text-sm">Review results will appear here once processing is complete</p>
        </div>
      )}
    </div>
  )
}
