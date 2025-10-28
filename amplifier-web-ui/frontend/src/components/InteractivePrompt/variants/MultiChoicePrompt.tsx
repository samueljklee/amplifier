import { useState } from 'react'
import type { PromptVariantProps } from '../types'

export default function MultiChoicePrompt({
  options = [],
  onSubmit,
  isLoading,
  disabled,
  metadata
}: PromptVariantProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const toggleSelection = (option: string) => {
    const newSelected = new Set(selected)
    if (newSelected.has(option)) {
      newSelected.delete(option)
    } else {
      newSelected.add(option)
    }
    setSelected(newSelected)
  }

  const selectAll = () => {
    setSelected(new Set(options))
  }

  const clearAll = () => {
    setSelected(new Set())
  }

  const handleSubmit = () => {
    if (selected.size > 0) {
      onSubmit(Array.from(selected))
    }
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2 max-h-[300px] overflow-y-auto">
        {options.map((option) => (
          <label
            key={option}
            className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
              selected.has(option)
                ? 'bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800'
                : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
            } ${disabled || isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <input
              type="checkbox"
              checked={selected.has(option)}
              onChange={() => toggleSelection(option)}
              disabled={disabled || isLoading}
              className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
            />
            <span className="text-sm text-gray-900 dark:text-white">
              {option}
            </span>
          </label>
        ))}
      </div>

      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600 dark:text-gray-400">
          {selected.size} of {options.length} selected
        </span>

        {options.length >= 5 && (
          <div className="flex gap-2">
            <button
              onClick={selectAll}
              disabled={disabled || isLoading}
              className="text-indigo-600 hover:text-indigo-700 font-medium disabled:opacity-50"
            >
              Select All
            </button>
            <button
              onClick={clearAll}
              disabled={disabled || isLoading}
              className="text-gray-600 hover:text-gray-700 font-medium disabled:opacity-50"
            >
              Clear All
            </button>
          </div>
        )}
      </div>

      <button
        onClick={handleSubmit}
        disabled={disabled || isLoading || selected.size === 0}
        className="w-full bg-indigo-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading
          ? 'Submitting...'
          : `Submit Selection${selected.size > 0 ? ` (${selected.size})` : ''}`}
      </button>

      {metadata?.helpText && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          💡 {metadata.helpText}
        </p>
      )}
    </div>
  )
}
