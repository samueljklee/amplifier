import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { Event } from '../types/api'
import AgentCard from './AgentCard'

interface Props {
  events: Event[]
}

interface AgentState {
  name: string
  status: 'idle' | 'running' | 'complete' | 'error'
  message: string
  progress?: number
}

interface StageState {
  name: string
  status: 'pending' | 'running' | 'complete'
  estimatedDuration?: number
  startTime?: string
  endTime?: string
}

export default function WorkflowViz({ events }: Props) {
  const [now, setNow] = useState(new Date())

  // Update "now" every second for live elapsed time
  useEffect(() => {
    const interval = setInterval(() => {
      setNow(new Date())
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  // Helper to calculate elapsed time
  const getElapsedTime = (startTime?: string, endTime?: string): string | null => {
    if (!startTime) return null
    const start = new Date(startTime)
    const end = endTime ? new Date(endTime) : now
    const seconds = Math.floor((end.getTime() - start.getTime()) / 1000)
    if (seconds < 60) return `${seconds}s`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}m ${remainingSeconds}s`
  }

  // Build agent states from events
  const agentStates = new Map<string, AgentState>()
  const stages: StageState[] = []
  let currentStage: string | null = null
  const stageMap = new Map<string, StageState>()

  // Track URL processing
  let urlsProcessed = 0
  let totalUrls = 0

  events.forEach((event) => {
    // Count URLs being processed
    if (event.type === 'log' && (event as any).message?.includes('Processing:')) {
      totalUrls++
    }
    if (event.type === 'file.created') {
      urlsProcessed++
    }

    // Handle agent events
    if (event.type === 'agent.start') {
      agentStates.set(event.agent, {
        name: event.agent,
        status: 'running',
        message: event.message,
      })
    } else if (event.type === 'agent.progress') {
      const existing = agentStates.get(event.agent)
      agentStates.set(event.agent, {
        name: event.agent,
        status: 'running',
        message: event.message,
        progress: event.progress,
      })
    } else if (event.type === 'agent.complete') {
      agentStates.set(event.agent, {
        name: event.agent,
        status: 'complete',
        message: event.message,
      })
    }
    // Handle stage transition events
    else if (event.type === 'stage.transition') {
      const toStage = (event as any).to_stage
      const fromStage = (event as any).from_stage
      const estimatedDuration = (event as any).estimated_duration
      const timestamp = (event as any).timestamp

      // Mark previous stage as complete (if transitioning away)
      if (fromStage && stageMap.has(fromStage)) {
        const stage = stageMap.get(fromStage)!
        stage.status = 'complete'
        stage.endTime = timestamp
      }

      // If toStage is null, we're completing the final stage
      if (!toStage && fromStage && stageMap.has(fromStage)) {
        const stage = stageMap.get(fromStage)!
        stage.status = 'complete'
        stage.endTime = timestamp
        currentStage = null
      }
      // Add new stage or update existing
      else if (toStage) {
        if (!stageMap.has(toStage)) {
          const stageState: StageState = {
            name: toStage,
            status: 'running',
            estimatedDuration,
            startTime: timestamp
          }
          stageMap.set(toStage, stageState)
          stages.push(stageState)
        } else {
          // Stage repeating (multi-URL processing) - keep it running
          stageMap.get(toStage)!.status = 'running'
        }
        currentStage = toStage
      }
    }
  })

  const agents = Array.from(agentStates.values())

  // Find latest progress event
  const latestProgress = events.filter(e => e.type === 'progress').slice(-1)[0] as any

  return (
    <div className="space-y-6">
      {/* URL Processing Progress */}
      {totalUrls > 1 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-blue-900 dark:text-blue-200">
              Processing URLs
            </span>
            <span className="text-sm text-blue-700 dark:text-blue-300">
              {urlsProcessed} / {totalUrls} complete
            </span>
          </div>
          <div className="mt-2 w-full bg-blue-200 dark:bg-blue-900 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${totalUrls > 0 ? (urlsProcessed / totalUrls) * 100 : 0}%` }}
            />
          </div>
        </div>
      )}

      {/* Stage Pipeline Visualization */}
      {stages.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            Current Stage
            {totalUrls > 1 && urlsProcessed < totalUrls && (
              <span className="ml-2 text-sm font-normal text-gray-500 dark:text-gray-400">
                (URL {urlsProcessed + 1}/{totalUrls})
              </span>
            )}
          </h3>
          <div className="flex items-center gap-2 flex-wrap">
            {stages.map((stage, idx) => {
              const elapsed = getElapsedTime(stage.startTime, stage.endTime)

              return (
                <div key={stage.name} className="flex items-center">
                  <div className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    stage.status === 'complete'
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                      : stage.status === 'running'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 animate-pulse'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                  }`}>
                    <div className="flex flex-col">
                      <div>
                        {stage.status === 'complete' && '✓ '}
                        {stage.status === 'running' && '⏳ '}
                        {stage.name}
                      </div>
                      {elapsed && (
                        <div className="text-xs opacity-70 mt-0.5">
                          {elapsed}
                        </div>
                      )}
                    </div>
                  </div>
                  {idx < stages.length - 1 && (
                    <div className="w-8 h-0.5 bg-gray-300 dark:bg-gray-600" />
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Progress Bar */}
      {latestProgress && (
        <div>
          <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
            <span>{latestProgress.message}</span>
            <span>{latestProgress.percent}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${latestProgress.percent}%` }}
            />
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {latestProgress.current} / {latestProgress.total}
          </div>
        </div>
      )}

      {/* Agent Cards */}
      {agents.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            Active Agents
          </h3>
          <AnimatePresence>
            {agents.map((agent) => (
              <AgentCard key={agent.name} agent={agent} />
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Show waiting message only if no stages and no agents */}
      {stages.length === 0 && agents.length === 0 && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          <p>Waiting for execution to start...</p>
        </div>
      )}
    </div>
  )
}
