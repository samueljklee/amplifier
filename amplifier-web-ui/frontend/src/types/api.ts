export interface Scenario {
  id: string
  name: string
  description: string
  path: string
  cli_command: string
  parameters: Parameter[]
  examples: Example[]
  metadata: ScenarioMetadata
}

export interface Parameter {
  name: string
  type: 'string' | 'path' | 'directory' | 'boolean' | 'number'
  required: boolean
  default?: any
  description: string
  validation?: Record<string, any>
}

export interface Example {
  title: string
  description: string
  command: string
  input_files?: Record<string, string>
}

export interface ScenarioMetadata {
  version?: string
  author?: string
  tags: string[]
}

export interface Execution {
  id: string
  scenario_id: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
  started_at: string
  completed_at?: string
  exit_code?: number
  error?: string
}

export interface WebSocketEvent {
  type: string
  execution_id: string
  timestamp?: string
}

export interface LogEvent extends WebSocketEvent {
  type: 'log'
  level: 'info' | 'warn' | 'error' | 'debug'
  message: string
}

export interface AgentStartEvent extends WebSocketEvent {
  type: 'agent.start'
  agent: string
  message: string
}

export interface AgentProgressEvent extends WebSocketEvent {
  type: 'agent.progress'
  agent: string
  message: string
  progress?: number
}

export interface AgentCompleteEvent extends WebSocketEvent {
  type: 'agent.complete'
  agent: string
  message: string
  result?: any
}

export interface ExecutionCompleteEvent extends WebSocketEvent {
  type: 'execution.complete'
  status: string
  exit_code: number
}

export interface ExecutionErrorEvent extends WebSocketEvent {
  type: 'execution.error'
  error: string
}

export interface ProgressEvent extends WebSocketEvent {
  type: 'progress'
  message: string
  current: number
  total: number
  percent: number
  metadata?: Record<string, any>
}

export interface FileCreatedEvent extends WebSocketEvent {
  type: 'file.created'
  path: string
  metadata?: Record<string, any>
}

export interface FileUpdatedEvent extends WebSocketEvent {
  type: 'file.updated'
  path: string
  metadata?: Record<string, any>
}

export interface InteractivePromptEvent extends WebSocketEvent {
  type: 'interactive.prompt'
  prompt_text: string
  prompt_type: string
  prompt_options: string[]
}

export interface StageTransitionEvent extends WebSocketEvent {
  type: 'stage.transition'
  from_stage?: string | null
  to_stage?: string | null
  estimated_duration?: number | null
}

export interface PreviewAvailableEvent extends WebSocketEvent {
  type: 'preview.available'
  preview_type: string
  preview_data: any
  metadata?: Record<string, any>
}

export interface StreamOutputEvent extends WebSocketEvent {
  type: 'stream.output'
  text: string
  source: 'assistant' | 'tool' | 'thinking' | 'agent'
}

export interface ToolCallEvent extends WebSocketEvent {
  type: 'tool.call'
  tool_name: string
  tool_input: any
  tool_use_id?: string
}

export interface ToolResultEvent extends WebSocketEvent {
  type: 'tool.result'
  tool_use_id: string
  tool_name: string
  result: any
  is_error: boolean
}

export type Event =
  | LogEvent
  | AgentStartEvent
  | AgentProgressEvent
  | AgentCompleteEvent
  | ExecutionCompleteEvent
  | ExecutionErrorEvent
  | ProgressEvent
  | FileCreatedEvent
  | FileUpdatedEvent
  | InteractivePromptEvent
  | StageTransitionEvent
  | PreviewAvailableEvent
  | StreamOutputEvent
  | ToolCallEvent
  | ToolResultEvent
