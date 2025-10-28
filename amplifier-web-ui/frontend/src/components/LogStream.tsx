import { useEffect, useRef } from 'react'
import type { Event } from '../types/api'

interface Props {
  events: Event[]
}

export default function LogStream({ events }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  // Include log events and interactive prompts (so questions show in log)
  const logEvents = events.filter((e) => e.type === 'log' || e.type === 'interactive.prompt')

  if (logEvents.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500 dark:text-gray-400 text-sm">
        No logs yet...
      </div>
    )
  }

  return (
    <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto">
      {logEvents.map((event, idx) => {
        // Handle interactive.prompt events
        if (event.type === 'interactive.prompt') {
          return (
            <div key={idx} className="text-blue-400 mb-1 flex items-center gap-1">
              <span className="text-gray-600">[prompt]</span>
              <svg className="w-4 h-4 inline-block" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
              </svg>
              <span>{(event as any).prompt_text || (event as any).prompt}</span>
            </div>
          )
        }

        // Handle log events
        if (event.type !== 'log') return null

        const levelColors = {
          info: 'text-gray-300',
          warn: 'text-yellow-400',
          error: 'text-red-400',
          debug: 'text-gray-500',
        }

        const color = levelColors[event.level] || 'text-gray-300'

        return (
          <div key={idx} className={`${color} mb-1`}>
            <span className="text-gray-600">[{event.level}]</span> {event.message}
          </div>
        )
      })}
      <div ref={bottomRef} />
    </div>
  )
}
