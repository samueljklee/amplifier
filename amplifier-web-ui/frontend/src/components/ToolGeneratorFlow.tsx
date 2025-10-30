import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import ConversationPhase from './ConversationPhase'
import GenerationPhase from './GenerationPhase'

type Phase = 'conversation' | 'generation'

export default function ToolGeneratorFlow() {
  const [searchParams] = useSearchParams()
  const [phase, setPhase] = useState<Phase>('conversation')
  const [executionId, setExecutionId] = useState<string | null>(null)

  // Use tool_generator (v2) if generatorV2 query param exists, otherwise use scenario_generator (default)
  const useGeneratorV2 = searchParams.has('generatorV2')
  const generatorScenario = useGeneratorV2 ? 'tool_generator' : 'scenario_generator'
  const parameterKey = useGeneratorV2 ? 'inline' : 'requirements'

  const startExecution = async (initialMessage: string) => {
    try {
      // Check if terminal mode
      if (!searchParams.has('customCreateScenario')) {
        // Use Claude CLI endpoint
        const execId = crypto.randomUUID()
        const response = await fetch('/api/claude/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            execution_id: execId,
            prompt: `/ultrathink-task ${initialMessage}`
          })
        })

        if (!response.ok) {
          throw new Error('Failed to start Claude CLI')
        }

        setExecutionId(execId)
      } else {
        // Use existing scenario_generator/tool_generator
        const response = await fetch(`/api/scenarios/${generatorScenario}/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            parameters: { [parameterKey]: initialMessage } // Use appropriate parameter key
          })
        })

        if (!response.ok) {
          throw new Error(`Failed to start ${generatorScenario}`)
        }

        const data = await response.json()
        setExecutionId(data.execution_id)
      }
    } catch (error) {
      console.error('Failed to start execution:', error)
    }
  }

  const handleConversationComplete = () => {
    setPhase('generation')
  }

  if (phase === 'conversation') {
    return (
      <ConversationPhase
        executionId={executionId}
        onComplete={handleConversationComplete}
        onStartExecution={startExecution}
      />
    )
  }

  return <GenerationPhase executionId={executionId!} />
}