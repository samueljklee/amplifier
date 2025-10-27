import { useState } from 'react'

interface Props {
  onApprove: () => void
  onRevise: (comments?: string) => void
  onSkip: () => void
  isProcessing?: boolean
  iteration: number
}

export default function ApprovalControls({
  onApprove,
  onRevise,
  onSkip,
  isProcessing = false,
  iteration,
}: Props) {
  const [showRevisionInput, setShowRevisionInput] = useState(false)
  const [comments, setComments] = useState('')

  const handleRevise = () => {
    if (showRevisionInput) {
      onRevise(comments.trim() || undefined)
      setComments('')
      setShowRevisionInput(false)
    } else {
      setShowRevisionInput(true)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (isProcessing) return

    if (e.key === 'Enter' && !e.shiftKey && !showRevisionInput) {
      e.preventDefault()
      onApprove()
    } else if (e.key === 'r' && !showRevisionInput && document.activeElement?.tagName !== 'INPUT') {
      e.preventDefault()
      setShowRevisionInput(true)
    } else if (e.key === 's' && !showRevisionInput && document.activeElement?.tagName !== 'INPUT') {
      e.preventDefault()
      onSkip()
    }
  }

  return (
    <div
      className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Iteration {iteration} - Review & Approve
      </h3>

      {showRevisionInput && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Revision Comments (optional)
          </label>
          <textarea
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            placeholder="Add specific feedback or inline comments..."
            className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-4 py-2 min-h-[100px]"
            autoFocus
          />
        </div>
      )}

      <div className="flex gap-3">
        <button
          onClick={onApprove}
          disabled={isProcessing || showRevisionInput}
          className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? 'Processing...' : '✓ Approve'}
        </button>

        <button
          onClick={handleRevise}
          disabled={isProcessing}
          className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {showRevisionInput ? 'Submit' : 'Revise'}
        </button>

        <button
          onClick={onSkip}
          disabled={isProcessing || showRevisionInput}
          className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Skip
        </button>
      </div>

      {showRevisionInput && (
        <button
          onClick={() => {
            setShowRevisionInput(false)
            setComments('')
          }}
          className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 mb-4"
        >
          Cancel
        </button>
      )}

      <p className="text-xs text-gray-500 dark:text-gray-400 mt-3">
        {showRevisionInput
          ? 'Describe what changes you want in the next iteration.'
          : 'Review the draft above and choose an action.'}
      </p>
    </div>
  )
}
