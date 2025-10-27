import { Link } from 'react-router-dom'
import { useWebSocket } from '../hooks/useWebSocket'
import ProgressStepper from './ProgressStepper'
import LogStream from './LogStream'

interface Props {
  executionId: string
}

const STAGES = [
  { id: 'specification', name: 'Building Specification', duration: 15 },
  { id: 'workspace', name: 'Setting Up Workspace', duration: 5 },
  { id: 'generation', name: 'Generating Code', duration: 180 },
  { id: 'validation', name: 'Validating Tool', duration: 30 },
  { id: 'complete', name: 'Complete', duration: 0 }
]

export default function GenerationPhase({ executionId }: Props) {
  const { events, isConnected } = useWebSocket(executionId)

  // Extract stage transitions
  const stageEvents = events.filter((e: any) => e.type === 'stage.transition')
  const currentStage = stageEvents[stageEvents.length - 1]?.to_stage || null

  // Check completion
  const isComplete = events.some((e: any) => e.type === 'execution.complete')

  // Extract generated tool name from events
  const toolName = extractToolName(events)

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-8">
        {isComplete ? 'Tool Created Successfully!' : 'Generating Your Tool...'}
      </h1>

      {/* Progress Stepper */}
      <div className="mb-8">
        <ProgressStepper stages={STAGES} currentStage={currentStage} />
      </div>

      {/* Completion Card */}
      {isComplete && toolName && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-3xl">✓</span>
            <div>
              <h3 className="text-lg font-semibold text-green-900 dark:text-green-100">
                Tool Created: {toolName}
              </h3>
              <p className="text-sm text-green-700 dark:text-green-300">
                Your new tool is ready to use
              </p>
            </div>
          </div>
          <Link
            to={`/scenarios/${toolName}`}
            className="inline-block px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            Try it now →
          </Link>
        </div>
      )}

      {/* Execution Logs */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Generation Logs</h3>
        <LogStream events={events} />
      </div>
    </div>
  )
}

// Helper to extract tool name from events
function extractToolName(events: any[]): string | null {
  // Look for log messages containing "Tool: {name}" or "tool_name: {name}"
  for (const event of events) {
    if (event.type === 'log' && event.message) {
      const toolMatch = event.message.match(/Tool:\s*(\w+)/)
      if (toolMatch) return toolMatch[1]

      const nameMatch = event.message.match(/tool_name:\s*(\w+)/)
      if (nameMatch) return nameMatch[1]
    }
  }

  return null
}