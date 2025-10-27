import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { FilePreviewIcon, ReviewIcon, EditIcon, DocumentIcon } from './Icons'

interface FileInput {
  mode: 'browse' | 'upload' | 'write'
  path?: string
  filename?: string
  content?: string
}

interface Props {
  label: string
  description?: string
  required?: boolean
  defaultPath?: string | null
  onChange: (content: FileInput) => void
  fileType?: 'markdown' | 'text' | 'any'
}

interface DirectoryItem {
  name: string
  type: 'file' | 'directory'
  path: string
  size?: number
}

interface DirectoryResponse {
  current_path: string
  parent_path: string | null
  items: DirectoryItem[]
}

export default function FilePicker({ label, description, required, defaultPath, onChange, fileType = 'any' }: Props) {
  const [activeTab, setActiveTab] = useState<'browse' | 'upload' | 'write'>('write')
  const [currentPath, setCurrentPath] = useState<string>(defaultPath || '/')
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [uploadedFile, setUploadedFile] = useState<{ path: string; filename: string } | null>(null)
  const [writeContent, setWriteContent] = useState<string>('')
  const [showMarkdownPreview, setShowMarkdownPreview] = useState(false)
  const [isDragging, setIsDragging] = useState(false)

  const storageKey = `filepicker-${label.replace(/\s+/g, '-').toLowerCase()}`

  useEffect(() => {
    const savedMode = localStorage.getItem(`${storageKey}-mode`)
    if (savedMode && (savedMode === 'browse' || savedMode === 'upload' || savedMode === 'write')) {
      setActiveTab(savedMode)
    }

    const savedDraft = localStorage.getItem(`${storageKey}-draft`)
    if (savedDraft) {
      setWriteContent(savedDraft)
    }
  }, [storageKey])

  useEffect(() => {
    localStorage.setItem(`${storageKey}-mode`, activeTab)
  }, [activeTab, storageKey])

  useEffect(() => {
    if (writeContent) {
      localStorage.setItem(`${storageKey}-draft`, writeContent)
    }
  }, [writeContent, storageKey])

  const { data: directory, isLoading: isBrowseLoading } = useQuery<DirectoryResponse>({
    queryKey: ['directory', currentPath],
    queryFn: async () => {
      const response = await fetch(`/api/files/browse?path=${encodeURIComponent(currentPath)}`)
      if (!response.ok) throw new Error('Failed to browse directory')
      return response.json()
    },
    enabled: activeTab === 'browse',
  })

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/files/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) throw new Error('Upload failed')
      return response.json()
    },
    onSuccess: (data) => {
      setUploadedFile({ path: data.path, filename: data.filename })
      onChange({
        mode: 'upload',
        path: data.path,
        filename: data.filename,
      })
    },
  })

  const handleTabChange = (tab: 'browse' | 'upload' | 'write') => {
    setActiveTab(tab)
    setSelectedFile(null)
    setUploadedFile(null)
    setWriteContent('')
  }

  const handleFileSelect = (file: DirectoryItem) => {
    if (file.type === 'directory') {
      setCurrentPath(file.path)
      return
    }

    if (fileType !== 'any') {
      const ext = file.name.split('.').pop()?.toLowerCase()
      if (fileType === 'markdown' && ext !== 'md') return
      if (fileType === 'text' && !['txt', 'md'].includes(ext || '')) return
    }

    setSelectedFile(file.path)
    onChange({
      mode: 'browse',
      path: file.path,
      filename: file.name,
    })
  }

  const handleGoUp = () => {
    if (directory?.parent_path) {
      setCurrentPath(directory.parent_path)
    }
  }

  const navigateToPath = (path: string) => {
    setCurrentPath(path)
  }

  const handleFileUpload = (file: File) => {
    if (fileType !== 'any') {
      const ext = file.name.split('.').pop()?.toLowerCase()
      if (fileType === 'markdown' && ext !== 'md') return
      if (fileType === 'text' && !['txt', 'md'].includes(ext || '')) return
    }

    uploadMutation.mutate(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileUpload(file)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleWriteContentChange = (content: string) => {
    setWriteContent(content)
    console.log(`📝 FilePicker [${label}] - Write content changed:`, content.substring(0, 50))
    onChange({
      mode: 'write',
      content,
    })
  }

  // Notify parent of initial state when in write mode
  useEffect(() => {
    if (activeTab === 'write') {
      // Always notify parent, even if content is empty
      onChange({
        mode: 'write',
        content: writeContent,
      })
    }
  }, []) // Only run on mount

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getWordCount = (text: string) => {
    return text.trim().split(/\s+/).filter(Boolean).length
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        {description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">{description}</p>
        )}

        <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700 mb-4">
          <button
            type="button"
            onClick={() => handleTabChange('browse')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'browse'
                ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
                : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
            }`}
          >
            <span className="flex items-center gap-1">
              <DocumentIcon size={16} /> Browse Files
            </span>
          </button>
          <button
            type="button"
            onClick={() => handleTabChange('upload')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'upload'
                ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
                : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
            }`}
          >
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Upload
            </span>
          </button>
          <button
            type="button"
            onClick={() => handleTabChange('write')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'write'
                ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
                : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
            }`}
          >
            <span className="flex items-center gap-1">
              <EditIcon size={16} /> Write Inline
            </span>
          </button>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 min-h-[300px]">
        {activeTab === 'browse' && (
          <div>
            {defaultPath && (
              <div className="mb-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <div className="text-sm text-blue-900 dark:text-blue-200 mb-2">
                  💡 Suggested location:
                </div>
                <code className="text-xs text-blue-700 dark:text-blue-300">
                  {defaultPath}
                </code>
                <button
                  type="button"
                  onClick={() => navigateToPath(defaultPath)}
                  className="ml-2 text-xs text-blue-600 hover:text-blue-700 underline"
                >
                  Go there
                </button>
              </div>
            )}

            {isBrowseLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-gray-500 dark:text-gray-400">Loading...</div>
              </div>
            ) : (
              <div>
                <div className="flex items-center gap-2 mb-4 pb-2 border-b border-gray-200 dark:border-gray-700">
                  <button
                    type="button"
                    onClick={handleGoUp}
                    disabled={!directory?.parent_path}
                    className="text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    ⬆ Up
                  </button>
                  <span className="text-xs text-gray-500 dark:text-gray-400 flex-1 truncate">
                    {directory?.current_path}
                  </span>
                </div>

                <div className="space-y-1 max-h-[400px] overflow-y-auto">
                  {directory?.items.map((item) => (
                    <button
                      key={item.path}
                      type="button"
                      onClick={() => handleFileSelect(item)}
                      className={`w-full text-left px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                        selectedFile === item.path
                          ? 'bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-300 dark:border-indigo-700'
                          : ''
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {item.type === 'directory' ? (
                          <DocumentIcon size={18} className="text-gray-600 dark:text-gray-400" />
                        ) : (
                          <FilePreviewIcon size={18} className="text-gray-600 dark:text-gray-400" />
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {item.name}
                          </div>
                          {item.size !== undefined && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              {formatFileSize(item.size)}
                            </div>
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>

                {selectedFile && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      Selected: <span className="font-medium">{selectedFile}</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'upload' && (
          <div>
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                isDragging
                  ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                  : 'border-gray-300 dark:border-gray-600'
              }`}
            >
              {uploadMutation.isPending ? (
                <div className="space-y-2">
                  <div className="text-gray-600 dark:text-gray-400">Uploading...</div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div className="bg-indigo-600 h-2 rounded-full animate-pulse w-1/2"></div>
                  </div>
                </div>
              ) : uploadedFile ? (
                <div className="space-y-2">
                  <div className="text-green-600 dark:text-green-400 text-lg">✓</div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {uploadedFile.filename}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Uploaded successfully
                  </div>
                </div>
              ) : (
                <>
                  <div className="text-4xl mb-4">📤</div>
                  <div className="text-gray-700 dark:text-gray-300 mb-2">
                    Drop your file here or
                  </div>
                  <label className="inline-block">
                    <input
                      type="file"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0]
                        if (file) handleFileUpload(file)
                      }}
                      accept={fileType === 'markdown' ? '.md' : fileType === 'text' ? '.txt,.md' : undefined}
                    />
                    <span className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 cursor-pointer inline-block">
                      Choose File
                    </span>
                  </label>
                  {fileType !== 'any' && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      Accepts: {fileType === 'markdown' ? '.md files' : 'text files (.txt, .md)'}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {activeTab === 'write' && (
          <div className="space-y-3">
            {fileType === 'markdown' && (
              <div className="flex justify-between items-center">
                <button
                  type="button"
                  onClick={() => setShowMarkdownPreview(!showMarkdownPreview)}
                  className="text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
                >
                  {showMarkdownPreview ? (
                    <span className="flex items-center gap-1">
                      <EditIcon size={14} /> Edit
                    </span>
                  ) : (
                    <span className="flex items-center gap-1">
                      <ReviewIcon size={14} /> Preview
                    </span>
                  )}
                </button>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {writeContent.length} chars · {getWordCount(writeContent)} words
                </div>
              </div>
            )}

            {!showMarkdownPreview ? (
              <textarea
                value={writeContent}
                onChange={(e) => handleWriteContentChange(e.target.value)}
                placeholder="Write or paste your content here..."
                className="w-full h-64 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm resize-y"
                required={required}
              />
            ) : (
              <div className="w-full h-64 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-900 overflow-y-auto prose prose-sm dark:prose-invert max-w-none">
                {writeContent ? (
                  <div className="whitespace-pre-wrap">{writeContent}</div>
                ) : (
                  <div className="text-gray-400 italic">Preview will appear here...</div>
                )}
              </div>
            )}

            {!showMarkdownPreview && (
              <div className="text-xs text-gray-500 dark:text-gray-400">
                💡 Your content is auto-saved as you type
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
