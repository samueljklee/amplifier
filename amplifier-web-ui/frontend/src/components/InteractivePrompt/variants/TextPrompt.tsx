import { useState } from 'react'
import type { PromptVariantProps } from '../types'

export default function TextPrompt({
  prompt,
  onSubmit,
  isLoading,
  disabled,
  metadata
}: PromptVariantProps) {
  const [value, setValue] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Basic validation
    if (metadata?.required && !value.trim()) {
      setError('Response is required')
      return
    }

    if (metadata?.minLength && value.length < metadata.minLength) {
      setError(`Minimum ${metadata.minLength} characters required`)
      return
    }

    if (metadata?.maxLength && value.length > metadata.maxLength) {
      setError(`Maximum ${metadata.maxLength} characters allowed`)
      return
    }

    setError(null)
    onSubmit(value.trim())  // Trim to remove trailing newlines
    setValue('')  // Clear the textarea after successful submission
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Enter submits, Shift+Enter adds newline
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={metadata?.placeholder}
        disabled={disabled || isLoading}
        className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-4 py-2 min-h-[100px]"
        aria-label={prompt}
        aria-required={metadata?.required}
        aria-invalid={!!error}
      />

      {metadata?.maxLength && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {value.length} / {metadata.maxLength} characters
        </p>
      )}

      {error && (
        <p className="text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}

      <div className="space-y-2">
        <button
          type="submit"
          disabled={disabled || isLoading || !value.trim()}
          className="w-full bg-indigo-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Submitting...' : 'Submit Response'}
        </button>

        <p className="text-xs text-center text-gray-500 dark:text-gray-400">
          Press <kbd className="px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">Enter</kbd> to submit, <kbd className="px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">Shift+Enter</kbd> for new line
        </p>
      </div>

      {metadata?.helpText && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          💡 {metadata.helpText}
        </p>
      )}
    </form>
  )
}
