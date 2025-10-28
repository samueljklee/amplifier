import { useState } from 'react'
import ConversationPhase from './ConversationPhase'
import GenerationPhase from './GenerationPhase'

type Phase = 'conversation' | 'generation'

export default function ToolGeneratorFlow() {
  const [phase, setPhase] = useState<Phase>('conversation')
  const [executionId, setExecutionId] = useState<string | null>(null)

  const startExecution = async (initialMessage: string) => {
    try {
      const response = await fetch('/api/scenarios/tool_generator/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parameters: { inline: initialMessage } // Pass user's message as inline requirements
        })
      })

      if (!response.ok) {
        throw new Error('Failed to start tool generator')
      }

      const data = await response.json()
      setExecutionId(data.execution_id)
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