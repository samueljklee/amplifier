import { useState, useEffect } from 'react'
import ConversationPhase from './ConversationPhase'
import GenerationPhase from './GenerationPhase'

type Phase = 'conversation' | 'generation'

export default function ToolGeneratorFlow() {
  const [phase, setPhase] = useState<Phase>('conversation')
  const [executionId, setExecutionId] = useState<string | null>(null)

  useEffect(() => {
    // Start execution immediately when component mounts
    startExecution()
  }, [])

  const startExecution = async () => {
    try {
      const response = await fetch('/api/scenarios/tool_generator/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parameters: { inline: '' } // Empty inline = conversation mode
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

  if (!executionId) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-600 dark:text-gray-400">
          Starting tool generator...
        </div>
      </div>
    )
  }

  if (phase === 'conversation') {
    return (
      <ConversationPhase
        executionId={executionId}
        onComplete={handleConversationComplete}
      />
    )
  }

  return <GenerationPhase executionId={executionId} />
}