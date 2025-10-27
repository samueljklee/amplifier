import { useQuery } from '@tanstack/react-query'
import type { Scenario } from '../types/api'

async function fetchScenarios(): Promise<Scenario[]> {
  const response = await fetch('/api/scenarios')
  if (!response.ok) {
    throw new Error('Failed to fetch scenarios')
  }
  const data = await response.json()
  return data.scenarios
}

export function useScenarios() {
  return useQuery({
    queryKey: ['scenarios'],
    queryFn: fetchScenarios,
  })
}

async function fetchScenario(scenarioId: string): Promise<Scenario> {
  const response = await fetch(`/api/scenarios/${scenarioId}`)
  if (!response.ok) {
    throw new Error('Failed to fetch scenario')
  }
  return response.json()
}

export function useScenario(scenarioId: string) {
  return useQuery({
    queryKey: ['scenario', scenarioId],
    queryFn: () => fetchScenario(scenarioId),
  })
}
