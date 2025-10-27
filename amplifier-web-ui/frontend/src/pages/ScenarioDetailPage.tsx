import { useParams } from 'react-router-dom'
import { useScenarios } from '../hooks/useScenarios'
import ScenarioForm from '../components/ScenarioForm'

export default function ScenarioDetailPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>()

  const { data: scenarios, isLoading } = useScenarios()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-600 dark:text-gray-400">Loading scenario...</div>
      </div>
    )
  }

  const scenario = scenarios?.find((s: any) => s.id === scenarioId)

  if (!scenario) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-red-600 dark:text-red-400">Scenario not found</div>
      </div>
    )
  }

  return <ScenarioForm scenario={scenario} />
}