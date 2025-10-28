import type { PromptVariantProps } from '../types'

export default function ApprovalPrompt({
  options = ['Yes', 'No'],
  onSubmit,
  isLoading,
  disabled
}: PromptVariantProps) {

  const handleClick = (option: string) => {
    if (!disabled && !isLoading) {
      onSubmit(option)
    }
  }

  const getButtonColor = (index: number) => {
    // First option = green (approve)
    if (index === 0) return 'bg-green-600 hover:bg-green-700'
    // Last option = gray (skip/neutral)
    if (index === options.length - 1 && options.length > 2) {
      return 'bg-gray-500 hover:bg-gray-600'
    }
    // Middle options or binary choice = indigo
    return 'bg-indigo-600 hover:bg-indigo-700'
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-3 flex-col sm:flex-row">
        {options.map((option, index) => (
          <button
            key={option}
            onClick={() => handleClick(option)}
            disabled={disabled || isLoading}
            className={`flex-1 ${getButtonColor(index)} text-white px-4 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {option}
          </button>
        ))}
      </div>

      <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
        ⌨️ Use keyboard shortcuts: Enter (first option) or Esc (last option)
      </p>
    </div>
  )
}
