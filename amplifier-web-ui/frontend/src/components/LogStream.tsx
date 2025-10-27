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

  const logEvents = events.filter((e) => e.type === 'log')

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
