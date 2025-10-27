import { motion } from 'framer-motion'

interface AgentState {
  name: string
  status: 'idle' | 'running' | 'complete' | 'error'
  message: string
  progress?: number
}

interface Props {
  agent: AgentState
}

const statusConfig = {
  idle: {
    icon: '⏸',
    color: 'bg-gray-100 dark:bg-gray-700',
    textColor: 'text-gray-700 dark:text-gray-300',
    borderColor: 'border-gray-300 dark:border-gray-600',
  },
  running: {
    icon: '⟳',
    color: 'bg-blue-100 dark:bg-blue-900/30',
    textColor: 'text-blue-700 dark:text-blue-300',
    borderColor: 'border-blue-300 dark:border-blue-600',
  },
  complete: {
    icon: '✓',
    color: 'bg-green-100 dark:bg-green-900/30',
    textColor: 'text-green-700 dark:text-green-300',
    borderColor: 'border-green-300 dark:border-green-600',
  },
  error: {
    icon: '✗',
    color: 'bg-red-100 dark:bg-red-900/30',
    textColor: 'text-red-700 dark:text-red-300',
    borderColor: 'border-red-300 dark:border-red-600',
  },
}

export default function AgentCard({ agent }: Props) {
  const config = statusConfig[agent.status]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={`border-l-4 ${config.borderColor} ${config.color} rounded-lg p-4`}
    >
      <div className="flex items-start gap-3">
        <div className={`text-2xl ${agent.status === 'running' ? 'agent-pulse' : ''}`}>
          {config.icon}
        </div>
        <div className="flex-1">
          <h4 className={`font-semibold ${config.textColor} capitalize`}>
            {agent.name.replace(/_/g, ' ')}
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{agent.message}</p>

          {agent.progress !== undefined && agent.status === 'running' && (
            <div className="mt-2 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
              <motion.div
                className="bg-blue-600 h-full"
                initial={{ width: 0 }}
                animate={{ width: `${agent.progress * 100}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
