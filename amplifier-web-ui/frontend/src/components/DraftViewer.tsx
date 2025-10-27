import hljs from 'highlight.js/lib/core'
import 'highlight.js/styles/github-dark.css'
import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// Import common languages
import bash from 'highlight.js/lib/languages/bash'
import css from 'highlight.js/lib/languages/css'
import javascript from 'highlight.js/lib/languages/javascript'
import json from 'highlight.js/lib/languages/json'
import markdown from 'highlight.js/lib/languages/markdown'
import python from 'highlight.js/lib/languages/python'
import sql from 'highlight.js/lib/languages/sql'
import typescript from 'highlight.js/lib/languages/typescript'
import xml from 'highlight.js/lib/languages/xml'

// Register languages
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('json', json)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('css', css)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('sql', sql)

interface Props {
  draftPath: string | null
  iteration: number
  wordCount?: number
  onViewModeChange?: (mode: 'raw' | 'preview') => void
}

interface FileContent {
  path: string
  content: string
  filename: string
}

export default function DraftViewer({ draftPath, iteration, wordCount, onViewModeChange }: Props) {
  const [fileContent, setFileContent] = useState<FileContent | null>(null)
  const [loadingFile, setLoadingFile] = useState(false)
  const [viewMode, setViewMode] = useState<'raw' | 'preview'>('preview')
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  const codeRefs = useRef<Map<string, HTMLElement>>(new Map())

  // Apply syntax highlighting after render
  useEffect(() => {
    codeRefs.current.forEach((el) => {
      if (el && !el.dataset.highlighted) {
        hljs.highlightElement(el)
        el.dataset.highlighted = 'true'
      }
    })
  })

  useEffect(() => {
    if (draftPath) {
      setLoadingFile(true)
      fetch(`/api/files/read?path=${encodeURIComponent(draftPath)}`)
        .then(res => res.json())
        .then(data => {
          setFileContent(data)
          setLoadingFile(false)
        })
        .catch(err => {
          console.error('Error loading file:', err)
          setLoadingFile(false)
        })
    } else {
      setFileContent(null)
    }
  }, [draftPath])

  useEffect(() => {
    if (onViewModeChange) {
      onViewModeChange(viewMode)
    }
  }, [viewMode, onViewModeChange])

  const handleCopyCode = async (code: string) => {
    try {
      await navigator.clipboard.writeText(code)
      setCopiedCode(code)
      setTimeout(() => setCopiedCode(null), 2000)
    } catch (err) {
      console.error('Failed to copy code:', err)
    }
  }

  const handleDownload = () => {
    if (!fileContent) return

    const blob = new Blob([fileContent.content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileContent.filename || `draft-iteration-${iteration}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (!draftPath) {
    return null
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Draft - Iteration {iteration}
          </h3>
          {wordCount !== undefined && (
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {wordCount.toLocaleString()} words
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Download Button */}
          {fileContent && (
            <button
              onClick={handleDownload}
              className="px-3 py-1.5 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700 transition-colors flex items-center gap-1.5"
              title="Download file"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </button>
          )}

          {/* View Mode Toggle */}
          <div className="flex bg-gray-200 dark:bg-gray-700 rounded-md p-1">
            <button
              onClick={() => setViewMode('preview')}
              className={`px-3 py-1 text-sm rounded transition-colors ${viewMode === 'preview'
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
            >
              Preview
            </button>
            <button
              onClick={() => setViewMode('raw')}
              className={`px-3 py-1 text-sm rounded transition-colors ${viewMode === 'raw'
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
            >
              Raw
            </button>
          </div>
        </div>
      </div>

      {loadingFile ? (
        <div className="flex items-center justify-center py-12 text-gray-500 dark:text-gray-400">
          Loading draft content...
        </div>
      ) : fileContent ? (
        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 overflow-auto max-h-[600px]">
          {viewMode === 'raw' ? (
            <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono leading-relaxed">
              {fileContent.content}
            </pre>
          ) : (
            <div className="max-w-none prose prose-slate dark:prose-invert prose-headings:font-bold prose-a:text-indigo-600 dark:prose-a:text-indigo-400 prose-table:table-auto">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    const codeString = String(children).replace(/\n$/, '')
                    const language = match ? match[1] : ''
                    const isInline = !match

                    if (isInline) {
                      return (
                        <code className="bg-gray-200 dark:bg-gray-700 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                          {children}
                        </code>
                      )
                    }

                    const codeId = `code-${Math.random().toString(36).substr(2, 9)}`

                    return (
                      <div className="relative group my-4">
                        {/* Copy button */}
                        <button
                          onClick={() => handleCopyCode(codeString)}
                          className="absolute right-2 top-2 px-2 py-1 text-xs rounded bg-gray-700 hover:bg-gray-600 text-white opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 z-10"
                          title="Copy code"
                        >
                          {copiedCode === codeString ? (
                            <>
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              Copied!
                            </>
                          ) : (
                            <>
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                              </svg>
                              Copy
                            </>
                          )}
                        </button>

                        <pre className="rounded-lg overflow-x-auto">
                          <code
                            ref={(el) => {
                              if (el) codeRefs.current.set(codeId, el)
                            }}
                            className={language ? `language-${language}` : ''}
                            {...props}
                          >
                            {codeString}
                          </code>
                        </pre>
                      </div>
                    )
                  },
                  // Enhance tables with better styling
                  table({ children }) {
                    return (
                      <div className="overflow-x-auto my-6 -mx-4 sm:mx-0">
                        <div className="inline-block min-w-full align-middle">
                          <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
                            <table className="min-w-full divide-y divide-gray-300 dark:divide-gray-700">
                              {children}
                            </table>
                          </div>
                        </div>
                      </div>
                    )
                  },
                  thead({ children }) {
                    return (
                      <thead className="bg-gray-100 dark:bg-gray-800">
                        {children}
                      </thead>
                    )
                  },
                  tbody({ children }) {
                    return (
                      <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-900">
                        {children}
                      </tbody>
                    )
                  },
                  tr({ children }) {
                    return (
                      <tr className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                        {children}
                      </tr>
                    )
                  },
                  th({ children }) {
                    return (
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wider">
                        {children}
                      </th>
                    )
                  },
                  td({ children }) {
                    return (
                      <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">
                        {children}
                      </td>
                    )
                  },
                }}
              >
                {fileContent.content}
              </ReactMarkdown>
            </div>
          )}
        </div>
      ) : (
        <div className="text-gray-500 dark:text-gray-400 text-center py-12">
          Failed to load draft content
        </div>
      )}
    </div>
  )
}
