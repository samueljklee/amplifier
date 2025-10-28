import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useScenarios } from '../hooks/useScenarios'
import ScenarioCard from './ScenarioCard'
import ScenarioForm from './ScenarioForm'
import ConfirmDeleteModal from './ConfirmDeleteModal'
import type { Scenario } from '../types/api'

export default function ScenarioList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: scenarios, isLoading, error } = useScenarios()
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null)
  const [scenarioToDelete, setScenarioToDelete] = useState<Scenario | null>(null)
  const [showAllScenarios, setShowAllScenarios] = useState(false)
  const [executionsExpanded, setExecutionsExpanded] = useState(true)

  // Fetch past executions
  const { data: executionsData } = useQuery({
    queryKey: ['executions'],
    queryFn: async () => {
      const response = await fetch('/api/executions?limit=10')
      if (!response.ok) throw new Error('Failed to fetch executions')
      return response.json()
    },
  })

  // Delete execution mutation
  const deleteExecutionMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await fetch(`/api/executions/${id}`, {
        method: 'DELETE',
      })
      if (!response.ok) throw new Error('Failed to delete execution')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] })
    },
  })

  // Delete scenario mutation
  const deleteScenarioMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await fetch(`/api/scenarios/${id}`, {
        method: 'DELETE',
      })
      if (!response.ok) throw new Error('Failed to delete scenario')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scenarios'] })
      setScenarioToDelete(null)
    },
  })

  const handleDeleteExecution = (executionId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    if (window.confirm('Delete this execution? This cannot be undone.')) {
      deleteExecutionMutation.mutate(executionId)
    }
  }

  const handleDeleteScenario = (scenario: Scenario) => {
    setScenarioToDelete(scenario)
  }

  const confirmDeleteScenario = () => {
    if (scenarioToDelete) {
      deleteScenarioMutation.mutate(scenarioToDelete.id)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" role="status" aria-label="Loading scenarios">
          <span className="sr-only">Loading scenarios...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-200">Failed to load scenarios: {String(error)}</p>
      </div>
    )
  }

  if (selectedScenario) {
    return (
      <div>
        <button
          onClick={() => setSelectedScenario(null)}
          className="mb-4 text-indigo-600 hover:text-indigo-800 dark:text-indigo-400"
        >
          ← Back to scenarios
        </button>
        <ScenarioForm scenario={selectedScenario} />
      </div>
    )
  }

  const pastExecutions = executionsData?.executions || []

  // No filtering - show all scenarios including tool_generator
  const filteredScenarios = scenarios

  // Show only first 6 scenarios by default
  const INITIAL_SCENARIO_COUNT = 6
  const visibleScenarios = showAllScenarios
    ? filteredScenarios
    : filteredScenarios?.slice(0, INITIAL_SCENARIO_COUNT)
  const hasMoreScenarios = (filteredScenarios?.length || 0) > INITIAL_SCENARIO_COUNT

  return (
    <div className="space-y-8">
      {/* Scenarios Section - Now First */}
      <div>
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">My Workflows</h2>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Pick a workflow to start creating
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {visibleScenarios?.map((scenario) => (
            <ScenarioCard
              key={scenario.id}
              scenario={scenario}
              onSelect={() => setSelectedScenario(scenario)}
              onDelete={() => handleDeleteScenario(scenario)}
            />
          ))}
        </div>

        {scenarios?.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400">No scenarios found</p>
          </div>
        )}

        {/* Show More/Less Button */}
        {hasMoreScenarios && (
          <div className="mt-6 text-center">
            <button
              onClick={() => setShowAllScenarios(!showAllScenarios)}
              className="inline-flex items-center gap-2 min-h-touch px-4 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-instant"
              aria-expanded={showAllScenarios}
              aria-label={showAllScenarios ? 'Show less scenarios' : `Show ${scenarios!.length - INITIAL_SCENARIO_COUNT} more scenarios`}
            >
              {showAllScenarios ? (
                <>
                  Show Less
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                  </svg>
                </>
              ) : (
                <>
                  Show {scenarios!.length - INITIAL_SCENARIO_COUNT} More
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Recent Work Section - Now Below */}
      {pastExecutions.length > 0 && (
        <div>
          <button
            onClick={() => setExecutionsExpanded(!executionsExpanded)}
            className="w-full mb-4 flex items-center justify-between group min-h-touch"
            aria-expanded={executionsExpanded}
            aria-label={executionsExpanded ? 'Hide recent work' : 'Show recent work'}
          >
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left">
                Recent Work
              </h2>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400 text-left">
                Continue from where you left off
              </p>
            </div>
            <svg
              className={`w-5 h-5 text-gray-500 transition-transform duration-responsive ${
                executionsExpanded ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {executionsExpanded && (
            <div className="grid grid-cols-1 gap-4">
              {pastExecutions.slice(0, 5).map((exec: any) => (
              <div
                key={exec.execution_id}
                className="relative group"
              >
                <button
                  onClick={() => navigate(`/executions/${exec.execution_id}`)}
                  className="w-full min-h-touch p-4 text-left bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-all duration-responsive hover:scale-[1.01] focus:scale-[1.01] border border-gray-200 dark:border-gray-700"
                  aria-label={`View execution: ${exec.scenario_id} completed ${new Date(exec.completed_at).toLocaleString()}`}
                >
                  <div className="flex-1 min-w-0 pr-8">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {exec.scenario_id}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200">
                        Completed
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                      {exec.preview || 'No preview available'}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                      {new Date(exec.completed_at).toLocaleString()}
                    </p>
                  </div>
                </button>
                <button
                  onClick={(e) => handleDeleteExecution(exec.execution_id, e)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 min-w-touch min-h-touch opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 p-2 rounded-full bg-white dark:bg-gray-700 text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-all duration-instant shadow-sm border border-gray-200 dark:border-gray-600"
                  aria-label={`Delete execution: ${exec.scenario_id}`}
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </button>
              </div>
            ))}
            </div>
          )}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <ConfirmDeleteModal
        isOpen={scenarioToDelete !== null}
        title="Delete Scenario"
        message={`Are you sure you want to delete "${scenarioToDelete?.name}"? This will permanently remove the scenario from your system and cannot be undone.`}
        onConfirm={confirmDeleteScenario}
        onCancel={() => setScenarioToDelete(null)}
        isDeleting={deleteScenarioMutation.isPending}
      />
    </div>
  )
}
