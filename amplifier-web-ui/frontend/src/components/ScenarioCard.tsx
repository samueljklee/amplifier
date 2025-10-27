import type { Scenario } from '../types/api'

interface Props {
  scenario: Scenario
  onSelect: () => void
  onDelete?: () => void
}

export default function ScenarioCard({ scenario, onSelect, onDelete }: Props) {
  // Truncate description to ensure consistent card heights
  const maxDescriptionLength = 120
  const description = scenario.description
  const truncatedDescription =
    description.length > maxDescriptionLength
      ? description.slice(0, maxDescriptionLength) + '...'
      : description
  const needsTooltip = description.length > maxDescriptionLength

  return (
    <div className="relative group">
      <button
        onClick={onSelect}
        className="w-full text-left bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-all duration-200 hover:scale-[1.01] focus:scale-[1.01] p-6 border border-gray-200 dark:border-gray-700 h-full flex flex-col"
      >
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          {scenario.name}
        </h3>
        <div className="relative group/description mb-4 flex-grow">
          <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">
            {truncatedDescription}
          </p>
          {/* Tooltip - positioned below description */}
          {needsTooltip && (
            <div className="absolute left-0 top-full mt-2 hidden group-hover/description:block z-10 w-64 p-3 text-sm text-white bg-gray-900 dark:bg-gray-700 rounded-lg shadow-lg">
              {description}
              {/* Arrow pointing up */}
              <div className="absolute bottom-full left-4 mb-[-1px] w-2 h-2 bg-gray-900 dark:bg-gray-700 rotate-45" />
            </div>
          )}
        </div>

        {scenario.metadata?.tags && scenario.metadata.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {scenario.metadata.tags.map((tag) => (
              <span
                key={tag}
                className="px-2 py-1 text-xs rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-500">
            {scenario.parameters.length} parameters
          </p>
        </div>
      </button>

      {/* Delete button - shows on hover/focus */}
      {onDelete && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 p-2 rounded-full bg-white dark:bg-gray-700 text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 focus:opacity-100 transition-all shadow-sm border border-gray-200 dark:border-gray-600"
          aria-label="Delete scenario"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      )}
    </div>
  )
}
