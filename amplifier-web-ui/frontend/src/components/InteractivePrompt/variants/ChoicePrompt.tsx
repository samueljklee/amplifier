import { useState } from 'react'
import type { PromptVariantProps } from '../types'

export default function ChoicePrompt({
  options = [],
  onSubmit,
  isLoading,
  disabled
}: PromptVariantProps) {
  const [selected, setSelected] = useState<string | null>(null)

  const handleSelect = (option: string) => {
    setSelected(option)
  }

  const handleSubmit = () => {
    if (selected) {
      onSubmit(selected)
    }
  }

  const useButtonGroup = options.length <= 5
  const useRadioList = options.length > 5

  if (useButtonGroup) {
    return (
      <div className="space-y-4">
        <div className="flex gap-3 flex-wrap">
          {options.map((option) => (
            <button
              key={option}
              onClick={() => {
                handleSelect(option)
                // Auto-submit on selection for button group
                onSubmit(option)
              }}
              disabled={disabled || isLoading}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selected === option
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/40'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {option}
            </button>
          ))}
        </div>
      </div>
    )
  }

  if (useRadioList) {
    return (
      <div className="space-y-4">
        <div className="space-y-2 max-h-[300px] overflow-y-auto">
          {options.map((option) => (
            <label
              key={option}
              className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                selected === option
                  ? 'bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800'
                  : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
              } ${disabled || isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <input
                type="radio"
                name="choice"
                value={option}
                checked={selected === option}
                onChange={() => handleSelect(option)}
                disabled={disabled || isLoading}
                className="w-4 h-4 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-sm text-gray-900 dark:text-white">
                {option}
              </span>
            </label>
          ))}
        </div>

        <button
          onClick={handleSubmit}
          disabled={disabled || isLoading || !selected}
          className="w-full bg-indigo-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Submitting...' : 'Confirm Selection'}
        </button>

        {selected && (
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Selected: {selected} ✓
          </p>
        )}
      </div>
    )
  }

  return null
}
