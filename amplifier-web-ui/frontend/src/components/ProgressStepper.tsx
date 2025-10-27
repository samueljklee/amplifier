import { useState, useEffect, useRef } from 'react'

interface Stage {
  id: string
  name: string
  duration: number // seconds
}

interface Props {
  stages: Stage[]
  currentStage: string | null
}

interface StageTimerProps {
  stageId: string
  currentStage: string | null
  isComplete: boolean
  onComplete: (stageId: string, duration: number) => void
  completedDuration?: number
}

function StageTimer({ stageId, currentStage, isComplete, onComplete, completedDuration }: StageTimerProps) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const startTimeRef = useRef<number | null>(null)

  useEffect(() => {
    const isCurrent = stageId === currentStage
    const wasCurrent = startTimeRef.current !== null

    // If this stage just became non-current, save its duration
    if (wasCurrent && !isCurrent) {
      const finalElapsed = Math.floor((Date.now() - startTimeRef.current!) / 1000)
      if (finalElapsed > 0) {
        onComplete(stageId, finalElapsed)
      }
      startTimeRef.current = null
      return
    }

    if (!isCurrent) {
      return
    }

    // Start timer for current stage
    startTimeRef.current = Date.now()
    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTimeRef.current!) / 1000)
      setElapsedSeconds(elapsed)
    }, 1000)

    return () => {
      clearInterval(interval)
    }
  }, [stageId, currentStage, onComplete])

  // Show completed duration for finished stages
  if (isComplete && completedDuration !== undefined) {
    const minutes = Math.floor(completedDuration / 60)
    const seconds = completedDuration % 60
    const formatted = `${minutes}:${seconds.toString().padStart(2, '0')}`

    return (
      <p className="text-xs text-green-600 dark:text-green-400 h-4 font-medium">
        {formatted}
      </p>
    )
  }

  // Show live timer for current stage
  if (stageId === currentStage) {
    const minutes = Math.floor(elapsedSeconds / 60)
    const seconds = elapsedSeconds % 60
    const formatted = `${minutes}:${seconds.toString().padStart(2, '0')}`

    return (
      <p className="text-xs text-indigo-600 dark:text-indigo-400 h-4 font-medium">
        {formatted}
      </p>
    )
  }

  return <p className="text-xs h-4"></p>
}

export default function ProgressStepper({ stages, currentStage }: Props) {
  const currentIndex = stages.findIndex(s => s.id === currentStage)
  const [stageDurations, setStageDurations] = useState<Record<string, number>>({})

  const handleStageComplete = (stageId: string, duration: number) => {
    setStageDurations(prev => ({
      ...prev,
      [stageId]: duration
    }))
  }

  return (
    <div className="flex items-center">
      {stages.map((stage, index) => {
        const isComplete = index < currentIndex
        const isCurrent = index === currentIndex

        return (
          <div key={stage.id} className="flex items-center flex-1">
            {/* Stage circle */}
            <div className="flex flex-col items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                  isComplete
                    ? 'bg-green-500 text-white'
                    : isCurrent
                    ? 'bg-indigo-600 text-white animate-pulse'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                }`}
              >
                {isComplete ? '✓' : index + 1}
              </div>

              {/* Stage label - fixed height to prevent jumping */}
              <div className="mt-2 text-center min-h-[3rem]">
                <p className={`text-sm font-medium ${
                  isCurrent ? 'text-indigo-600 dark:text-indigo-400' : 'text-gray-600 dark:text-gray-400'
                }`}>
                  {stage.name}
                </p>
                {/* Live timer - always takes up space */}
                <StageTimer
                  stageId={stage.id}
                  currentStage={currentStage}
                  isComplete={isComplete}
                  onComplete={handleStageComplete}
                  completedDuration={stageDurations[stage.id]}
                />
              </div>
            </div>

            {/* Connector line */}
            {index < stages.length - 1 && (
              <div
                className={`flex-1 h-1 mx-2 ${
                  isComplete ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700'
                }`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}