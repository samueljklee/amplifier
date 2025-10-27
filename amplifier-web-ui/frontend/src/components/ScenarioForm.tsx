import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Scenario } from '../types/api'
import FilePicker from './FilePicker'
import MultiFilePicker, { type FileInput } from './MultiFilePicker'

interface Props {
  scenario: Scenario
}

export default function ScenarioForm({ scenario }: Props) {
  const navigate = useNavigate()
  const [parameters, setParameters] = useState<Record<string, any>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [urlList, setUrlList] = useState<string[]>([''])
  const [fileInputs, setFileInputs] = useState<Record<string, any>>({}) // For web_to_md multiple URLs

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      // Debug: Log what we're about to send
      console.log('📤 Form submission - parameters:', parameters)
      console.log('📤 Form submission - fileInputs:', fileInputs)

      // For web_to_md, handle multiple URLs
      const finalParams = { ...parameters }
      if (scenario.id === 'web_to_md') {
        // Filter out empty URLs and set as url parameter
        const validUrls = urlList.filter(url => url.trim())
        if (validUrls.length > 0) {
          finalParams.url = validUrls[0] // Primary URL
          // Add additional URLs as url2, url3, etc.
          validUrls.slice(1).forEach((url, idx) => {
            finalParams[`url${idx + 2}`] = url
          })
        }
      }

      const response = await fetch(`/api/scenarios/${scenario.id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parameters: finalParams }),
      })

      if (!response.ok) {
        throw new Error('Failed to start execution')
      }

      const data = await response.json()
      navigate(`/executions/${data.execution_id}`)
    } catch (err) {
      setError(String(err))
      setIsSubmitting(false)
    }
  }

  const handleParameterChange = (name: string, value: any) => {
    setParameters((prev) => ({ ...prev, [name]: value }))
  }

  const handleUrlChange = (index: number, value: string) => {
    const newUrls = [...urlList]
    newUrls[index] = value
    setUrlList(newUrls)
  }

  const addUrlField = () => {
    setUrlList([...urlList, ''])
  }

  const removeUrlField = (index: number) => {
    if (urlList.length > 1) {
      setUrlList(urlList.filter((_, i) => i !== index))
    }
  }

  const handleFileInputChange = (name: string, fileInput: any) => {
    console.log(`📝 ScenarioForm [${name}] - File input changed:`, fileInput)
    setFileInputs(prev => ({ ...prev, [name]: fileInput }))

    if (fileInput.mode === 'write') {
      // Always set parameters for write mode, even if content is empty
      // This ensures the form knows we're in write mode and waiting for content
      console.log(`📝 ScenarioForm [${name}] - Setting inline content (${fileInput.content?.length || 0} chars)`)
      setParameters(prev => ({
        ...prev,
        [name]: '__INLINE__',
        [`${name}_content`]: fileInput.content || ''
      }))
    } else if (fileInput.path) {
      console.log(`📝 ScenarioForm [${name}] - Setting file path: ${fileInput.path}`)
      setParameters(prev => ({ ...prev, [name]: fileInput.path }))
    } else {
      console.log(`📝 ScenarioForm [${name}] - Clearing parameter (no path or content)`)
      // Clear the parameter if no valid input
      setParameters(prev => {
        const updated = { ...prev }
        delete updated[name]
        delete updated[`${name}_content`]
        return updated
      })
    }
  }

  const handleMultiFileChange = (name: string, files: FileInput[]) => {
    setFileInputs(prev => ({ ...prev, [name]: files }))

    console.log(`📂 MultiFilePicker [${name}] - Files changed:`, files)

    const hasInline = files.some(f => f.mode === 'write')
    if (hasInline) {
      // Has inline content - create temp files
      setParameters(prev => ({
        ...prev,
        [name]: '__INLINE__',
        [`${name}_files`]: files.map(f => ({
          content: f.content,
          filename: f.filename || `file_${files.indexOf(f)}.md`
        }))
      }))
    } else if (files.length === 1 && files[0].path) {
      // Single path - likely a directory selection, use it directly
      setParameters(prev => ({
        ...prev,
        [name]: files[0].path
      }))
    } else {
      // Multiple paths - join with commas (for scenarios that accept multiple files)
      setParameters(prev => ({
        ...prev,
        [name]: files.map(f => f.path).filter(Boolean).join(',')
      }))
    }
  }

  const inferFileType = (paramName: string): 'markdown' | 'text' | 'any' => {
    if (paramName.includes('idea') || paramName.includes('brain') || paramName.includes('writing')) {
      return 'markdown'
    }
    return 'any'
  }

  const getDefaultPath = (scenarioId: string, paramName: string): string | null => {
    if (scenarioId === 'blog_writer') {
      if (paramName === 'idea') {
        return '/Users/samule/repo/amplifier/.data/blog_ideas'
      }
      if (paramName === 'writings_dir') {
        return '/Users/samule/repo/amplifier/content'
      }
    }

    if (scenarioId === 'web_to_md') {
      if (paramName === 'output') {
        return '/Users/samule/repo/amplifier/.data/content/sites'
      }
    }

    if (paramName.includes('idea') || paramName.includes('brain')) {
      return '/Users/samule/repo/amplifier/.data'
    }
    if (paramName.includes('writing') || paramName.includes('content')) {
      return '/Users/samule/repo/amplifier/content'
    }
    if (paramName.includes('output')) {
      return '/Users/samule/repo/amplifier/.data'
    }

    return null
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
        {scenario.name}
      </h2>
      <p className="text-gray-600 dark:text-gray-400 mb-6">{scenario.description}</p>

      {error && (
        <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-4">
          <p className="text-red-800 dark:text-red-200 text-sm">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Special handling for web_to_md URLs */}
        {scenario.id === 'web_to_md' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              URLs to Convert <span className="text-red-500 ml-1">*</span>
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
              Enter one or more web page URLs to convert to markdown
            </p>

            {urlList.map((url, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => handleUrlChange(index, e.target.value)}
                  placeholder="https://example.com/article"
                  required={index === 0}
                  className="flex-1 rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-4 py-2"
                />
                {index > 0 && (
                  <button
                    type="button"
                    onClick={() => removeUrlField(index)}
                    className="px-3 py-2 text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}

            <button
              type="button"
              onClick={addUrlField}
              className="mt-2 text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
            >
              + Add another URL
            </button>
          </div>
        )}

        {scenario.parameters.map((param) => {
          // Skip 'url' parameter for web_to_md as we handle it specially above
          if (scenario.id === 'web_to_md' && param.name === 'url') {
            return null
          }

          // Skip unnecessary parameters for blog_writer (web UI handles these differently)
          if (scenario.id === 'blog_writer') {
            const skipParams = ['output', 'resume', 'reset', 'verbose', 'max_iterations', 'instructions']
            if (skipParams.includes(param.name)) {
              return null
            }
          }

          return (
            <div key={param.name}>
              {/* FilePicker and MultiFilePicker show their own labels, others need labels */}
              {param.type !== 'path' && param.type !== 'directory' && (
                <>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {param.name}
                    {param.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{param.description}</p>
                </>
              )}

              {param.type === 'boolean' ? (
                <input
                  type="checkbox"
                  checked={parameters[param.name] || false}
                  onChange={(e) => handleParameterChange(param.name, e.target.checked)}
                  className="h-4 w-4 text-indigo-600 rounded"
                />
              ) : param.type === 'number' ? (
                <input
                  type="number"
                  value={parameters[param.name] || param.default || ''}
                  onChange={(e) => handleParameterChange(param.name, e.target.value)}
                  required={param.required}
                  className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              ) : param.type === 'path' ? (
                <FilePicker
                  label={scenario.id === 'blog_writer' && param.name === 'idea' ? 'Your Idea' : param.name}
                  description={param.description}
                  required={param.required}
                  defaultPath={getDefaultPath(scenario.id, param.name)}
                  onChange={(fileInput) => handleFileInputChange(param.name, fileInput)}
                  fileType={inferFileType(param.name)}
                />
              ) : param.type === 'directory' ? (
                <MultiFilePicker
                  label={scenario.id === 'blog_writer' && param.name === 'writings_dir' ? 'Your Writing Samples' : param.name}
                  description={scenario.id === 'blog_writer' && param.name === 'writings_dir'
                    ? 'Add 2-3 examples of your writing so we can match your style'
                    : param.description}
                  required={param.required}
                  minFiles={1}
                  defaultDirectory={getDefaultPath(scenario.id, param.name)}
                  onChange={(files) => handleMultiFileChange(param.name, files)}
                  fileType={inferFileType(param.name)}
                />
              ) : (
                <input
                  type="text"
                  value={parameters[param.name] || param.default || ''}
                  onChange={(e) => handleParameterChange(param.name, e.target.value)}
                  required={param.required}
                  className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-4 py-2"
                />
              )}
            </div>
          )
        })}

        {/* Show examples only for non-blog_writer scenarios */}
        {scenario.id !== 'blog_writer' && scenario.examples.length > 0 && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded p-4">
            <h4 className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-2">Examples</h4>
            {scenario.examples.map((example, idx) => (
              <div key={idx} className="text-xs text-blue-800 dark:text-blue-300 mb-1">
                <code className="bg-blue-100 dark:bg-blue-900/40 px-1 rounded">{example.command}</code>
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex-1 bg-indigo-600 text-white px-6 py-3 rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            {isSubmitting ? 'Starting...' : '▶ Run Scenario'}
          </button>
        </div>
      </form>
    </div>
  )
}
