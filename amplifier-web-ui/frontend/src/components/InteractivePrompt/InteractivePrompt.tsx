import { motion } from 'framer-motion'
import TextPrompt from './variants/TextPrompt'
import ApprovalPrompt from './variants/ApprovalPrompt'
import ChoicePrompt from './variants/ChoicePrompt'
import MultiChoicePrompt from './variants/MultiChoicePrompt'
import type { InteractivePromptProps } from './types'

const promptVariants = {
  hidden: {
    opacity: 0,
    y: 20,
    scale: 0.95
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1]
    }
  }
}

export default function InteractivePrompt({
  prompt,
  promptType,
  options,
  onSubmit,
  onCancel,
  isLoading,
  disabled,
  metadata
}: InteractivePromptProps) {

  const renderVariant = () => {
    const sharedProps = {
      prompt,
      options,
      onSubmit,
      onCancel,
      isLoading,
      disabled,
      metadata
    }

    switch (promptType) {
      case 'text':
        return <TextPrompt {...sharedProps} />
      case 'approval':
        return <ApprovalPrompt {...sharedProps} />
      case 'choice':
        return <ChoicePrompt {...sharedProps} />
      case 'multi-choice':
        return <MultiChoicePrompt {...sharedProps} />
      default:
        return <div>Unknown prompt type</div>
    }
  }

  return (
    <motion.div
      variants={promptVariants}
      initial="hidden"
      animate="visible"
      className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 relative"
      role="region"
      aria-label="Interactive prompt"
      aria-busy={isLoading}
    >
      {/* Prompt header */}
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        {metadata?.iteration && `Iteration ${metadata.iteration} - `}
        {prompt}
      </h3>

      {/* Variant-specific UI */}
      {renderVariant()}

      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-white/80 dark:bg-gray-800/80 rounded-lg flex items-center justify-center z-10">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-gray-700 dark:text-gray-300 font-medium">
              Processing your response...
            </span>
          </div>
        </div>
      )}
    </motion.div>
  )
}
