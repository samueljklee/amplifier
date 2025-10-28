export type PromptType = 'text' | 'approval' | 'choice' | 'multi-choice'

export interface InteractivePromptProps {
  // Core
  prompt: string
  promptType: PromptType
  options?: string[]

  // Callbacks
  onSubmit: (response: string | string[]) => void
  onCancel?: () => void

  // State
  isLoading?: boolean
  disabled?: boolean

  // Metadata
  metadata?: {
    iteration?: number
    required?: boolean
    minLength?: number
    maxLength?: number
    placeholder?: string
    helpText?: string
  }
}

export interface PromptVariantProps {
  prompt: string
  options?: string[]
  onSubmit: (response: string | string[]) => void
  onCancel?: () => void
  isLoading?: boolean
  disabled?: boolean
  metadata?: InteractivePromptProps['metadata']
}

export interface ValidationResult {
  isValid: boolean
  error?: string
}