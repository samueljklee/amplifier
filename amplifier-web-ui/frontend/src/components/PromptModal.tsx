import { useState } from 'react'

interface PromptModalProps {
  prompt: string
  options: string[]
  promptType: string
  onSubmit: (response: string) => void
  onCancel: () => void
}

export default function PromptModal({
  prompt,
  options,
  promptType,
  onSubmit,
  onCancel
}: PromptModalProps) {
  const [customResponse, setCustomResponse] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (response: string) => {
    if (!response.trim()) return

    setIsSubmitting(true)
    try {
      await onSubmit(response)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && customResponse.trim()) {
      handleSubmit(customResponse)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 max-w-lg w-full border border-gray-200 dark:border-gray-700 animate-in fade-in zoom-in duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">💬</span>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
              {promptType === 'approval' ? 'Review Required' : 'Input Required'}
            </h3>
          </div>
          <p className="text-gray-600 dark:text-gray-400 text-sm mt-2">
            {prompt}
          </p>
        </div>

        {/* Options or Custom Input */}
        {options && options.length > 0 ? (
          <div className="space-y-2 mb-6">
            {options.map(opt => (
              <button
                key={opt}
                onClick={() => handleSubmit(opt)}
                disabled={isSubmitting}
                className="w-full p-4 text-left rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-indigo-500 dark:hover:border-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900 dark:text-white capitalize">
                    {opt}
                  </span>
                  <span className="text-gray-400 group-hover:text-indigo-500 transition-colors">
                    →
                  </span>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="mb-6">
            <input
              type="text"
              value={customResponse}
              onChange={(e) => setCustomResponse(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your response..."
              disabled={isSubmitting}
              autoFocus
              className="w-full p-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50 transition-all"
            />
            <button
              onClick={() => handleSubmit(customResponse)}
              disabled={!customResponse.trim() || isSubmitting}
              className="mt-3 w-full p-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Response'}
            </button>
          </div>
        )}

        {/* Cancel Button */}
        <button
          onClick={onCancel}
          disabled={isSubmitting}
          className="w-full text-center text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50 transition-colors"
        >
          Cancel
        </button>

        {/* Loading Indicator */}
        {isSubmitting && (
          <div className="mt-4 flex items-center justify-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <span>Sending response...</span>
          </div>
        )}
      </div>
    </div>
  )
}
