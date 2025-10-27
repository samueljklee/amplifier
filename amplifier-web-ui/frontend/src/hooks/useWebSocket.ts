import { useEffect, useRef, useState } from 'react'
import type { Event } from '../types/api'

export function useWebSocket(executionId: string | null) {
  const [events, setEvents] = useState<Event[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const ws = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!executionId) return

    const websocket = new WebSocket(`ws://localhost:8000/api/ws/executions/${executionId}`)

    websocket.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type !== 'heartbeat' && data.type !== 'connected') {
        setEvents((prev) => [...prev, data])
      }
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsConnected(false)
    }

    ws.current = websocket

    return () => {
      websocket.close()
    }
  }, [executionId])

  return { events, isConnected }
}
