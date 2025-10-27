import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes, Link, useLocation } from 'react-router-dom'
import ScenarioList from './components/ScenarioList'
import ExecutionView from './components/ExecutionView'
import BlogWriterExecutionView from './components/BlogWriterExecutionView'
import ToolGeneratorFlow from './components/ToolGeneratorFlow'
import ScenarioDetailPage from './pages/ScenarioDetailPage'
import { StudioIcon, CreateIcon } from './components/Icons'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'

const queryClient = new QueryClient()

// Rotating taglines for the header subtitle
const TAGLINES = [
  'Create powerful workflows',
  'Turn ideas into workflows',
  'Where workflows come alive',
] as const

// Pick random tagline on initial load
const getRandomTagline = () => TAGLINES[Math.floor(Math.random() * TAGLINES.length)]

function Navigation() {
  const location = useLocation()

  const isActive = (path: string) => location.pathname === path
  const linkClass = (path: string) => `px-4 py-2 rounded-md text-sm font-medium transition-colors ${isActive(path)
    ? 'bg-indigo-600 text-white'
    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
    }`

  return (
    <nav className="flex gap-2">
      <Link to="/" className={linkClass('/')}>
        Scenarios
      </Link>
      <Link to="/create" className={linkClass('/create')}>
        <span className="inline-flex items-center gap-2">
          <CreateIcon size={16} />
          Create New
        </span>
      </Link>
    </nav>
  )
}

function ExecutionRouter() {
  const { executionId } = useParams<{ executionId: string }>()
  const { data: execution, isLoading } = useQuery({
    queryKey: ['execution', executionId],
    queryFn: async () => {
      const response = await fetch(`/api/executions/${executionId}`)
      if (!response.ok) throw new Error('Failed to fetch execution')
      return response.json()
    },
    enabled: !!executionId,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-600 dark:text-gray-400">Loading execution...</div>
      </div>
    )
  }

  if (!execution) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-red-600 dark:text-red-400">Execution not found</div>
      </div>
    )
  }

  if (execution.scenario_id === 'blog_writer') {
    return <BlogWriterExecutionView />
  }

  return <ExecutionView />
}

function App() {
  // Initialize with random tagline
  const [taglineIndex, setTaglineIndex] = useState(() =>
    TAGLINES.indexOf(getRandomTagline())
  )

  // Easter egg: Click to cycle through taglines
  const cycleTagline = () => {
    setTaglineIndex((prev) => (prev + 1) % TAGLINES.length)
  }

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
          <header className="bg-white dark:bg-gray-800 shadow">
            <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                    <StudioIcon size={32} />
                    Amplifier Studio
                  </h1>
                  <p
                    onClick={cycleTagline}
                    className="mt-1 text-sm text-gray-600 dark:text-gray-400 cursor-pointer hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors select-none"
                    title="Click to see another tagline 🎲"
                  >
                    {TAGLINES[taglineIndex]}
                  </p>
                </div>
                <Navigation />
              </div>
            </div>
          </header>

          <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <Routes>
              <Route path="/" element={<ScenarioList />} />
              <Route path="/scenarios/:scenarioId" element={<ScenarioDetailPage />} />
              <Route path="/executions/:executionId" element={<ExecutionRouter />} />
              <Route path="/create" element={<ToolGeneratorFlow />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
