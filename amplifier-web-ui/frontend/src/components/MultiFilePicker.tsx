import { useState, useEffect } from 'react'

export interface FileInput {
  id: string
  mode: 'browse' | 'upload' | 'write'
  path?: string
  filename?: string
  content?: string
}

interface Props {
  label: string
  description?: string
  required?: boolean
  minFiles?: number
  maxFiles?: number
  defaultDirectory?: string | null
  onChange: (files: FileInput[]) => void
  fileType?: 'markdown' | 'text' | 'any'
}

export default function MultiFilePicker({
  label,
  description,
  required = false,
  minFiles = 1,
  maxFiles,
  defaultDirectory,
  onChange,
  fileType = 'any',
}: Props) {
  const [files, setFiles] = useState<FileInput[]>(() => {
    const initial: FileInput[] = []
    for (let i = 0; i < minFiles; i++) {
      initial.push({
        id: crypto.randomUUID(),
        mode: 'write',  // Default to write mode for inline content
      })
    }
    return initial
  })

  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(
    new Set(files.map((f) => f.id))
  )

  useEffect(() => {
    onChange(files)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [files])

  const handleAddFile = () => {
    if (maxFiles && files.length >= maxFiles) return

    const newFile: FileInput = {
      id: crypto.randomUUID(),
      mode: 'browse',
    }
    setFiles([...files, newFile])
    setExpandedFiles(new Set([...expandedFiles, newFile.id]))
  }

  const handleRemoveFile = (id: string) => {
    if (files.length <= minFiles) return

    setFiles(files.filter((f) => f.id !== id))
    const newExpanded = new Set(expandedFiles)
    newExpanded.delete(id)
    setExpandedFiles(newExpanded)
  }

  const handleModeChange = (id: string, mode: 'browse' | 'upload' | 'write') => {
    setFiles(
      files.map((f) =>
        f.id === id
          ? { id: f.id, mode, path: undefined, filename: undefined, content: undefined }
          : f
      )
    )
  }

  const handlePathChange = (id: string, path: string) => {
    setFiles(
      files.map((f) =>
        f.id === id ? { ...f, path, filename: path.split('/').pop() } : f
      )
    )
  }

  const handleFileUpload = (id: string, file: File) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const content = e.target?.result as string
      setFiles(
        files.map((f) =>
          f.id === id ? { ...f, filename: file.name, content } : f
        )
      )
    }
    reader.readAsText(file)
  }

  const handleContentChange = (id: string, content: string) => {
    setFiles(files.map((f) => (f.id === id ? { ...f, content } : f)))
  }

  const handleFilenameChange = (id: string, filename: string) => {
    setFiles(files.map((f) => (f.id === id ? { ...f, filename } : f)))
  }

  const toggleExpand = (id: string) => {
    const newExpanded = new Set(expandedFiles)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedFiles(newExpanded)
  }

  const getFileExtension = () => {
    if (fileType === 'markdown') return '.md'
    if (fileType === 'text') return '.txt'
    return ''
  }

  const getAcceptAttribute = () => {
    if (fileType === 'markdown') return '.md,.markdown'
    if (fileType === 'text') return '.txt'
    return '*'
  }

  const isFileComplete = (file: FileInput): boolean => {
    if (file.mode === 'browse') return !!file.path
    if (file.mode === 'upload') return !!file.content && !!file.filename
    if (file.mode === 'write') return !!file.content && !!file.filename
    return false
  }

  const completeFiles = files.filter(isFileComplete).length
  const hasMinimumFiles = completeFiles >= minFiles
  const showValidation = required && !hasMinimumFiles

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
          {minFiles > 1 && (
            <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
              (min: {minFiles}
              {maxFiles && `, max: ${maxFiles}`})
            </span>
          )}
        </label>
        {description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">{description}</p>
        )}
      </div>

      <div className="space-y-3">
        {files.map((file, index) => {
          const isExpanded = expandedFiles.has(file.id)
          const isComplete = isFileComplete(file)

          return (
            <div
              key={file.id}
              className="border border-gray-300 dark:border-gray-600 rounded-lg p-4 bg-gray-50 dark:bg-gray-800"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    File {index + 1}
                  </span>
                  {isComplete && !isExpanded && (
                    <span className="text-xs text-green-600 dark:text-green-400">
                      {file.filename || file.path?.split('/').pop()}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {isComplete && (
                    <button
                      type="button"
                      onClick={() => toggleExpand(file.id)}
                      className="text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300"
                    >
                      {isExpanded ? 'Collapse' : 'Expand'}
                    </button>
                  )}
                  {files.length > minFiles && (
                    <button
                      type="button"
                      onClick={() => handleRemoveFile(file.id)}
                      className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                    >
                      ✕
                    </button>
                  )}
                </div>
              </div>

              {isExpanded && (
                <>
                  <div className="flex gap-2 mb-3">
                    <button
                      type="button"
                      onClick={() => handleModeChange(file.id, 'browse')}
                      className={`px-3 py-1 text-sm rounded ${
                        file.mode === 'browse'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                      }`}
                    >
                      Browse
                    </button>
                    <button
                      type="button"
                      onClick={() => handleModeChange(file.id, 'upload')}
                      className={`px-3 py-1 text-sm rounded ${
                        file.mode === 'upload'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                      }`}
                    >
                      Upload
                    </button>
                    <button
                      type="button"
                      onClick={() => handleModeChange(file.id, 'write')}
                      className={`px-3 py-1 text-sm rounded ${
                        file.mode === 'write'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                      }`}
                    >
                      Write
                    </button>
                  </div>

                  {file.mode === 'browse' && (
                    <div className="space-y-2">
                      {defaultDirectory && (
                        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                          <div className="text-sm text-blue-900 dark:text-blue-200 mb-2">
                            💡 Suggested location:
                          </div>
                          <code className="text-xs text-blue-700 dark:text-blue-300">
                            {defaultDirectory}
                          </code>
                          <button
                            type="button"
                            onClick={() => handlePathChange(file.id, defaultDirectory)}
                            className="ml-2 text-xs text-blue-600 hover:text-blue-700 underline"
                          >
                            Use this
                          </button>
                        </div>
                      )}
                      <input
                        type="text"
                        value={file.path || ''}
                        onChange={(e) => handlePathChange(file.id, e.target.value)}
                        placeholder={`/path/to/file${getFileExtension()}`}
                        className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-3 py-2 text-sm"
                      />
                    </div>
                  )}

                  {file.mode === 'upload' && (
                    <div>
                      <input
                        type="file"
                        accept={getAcceptAttribute()}
                        onChange={(e) => {
                          const uploadedFile = e.target.files?.[0]
                          if (uploadedFile) handleFileUpload(file.id, uploadedFile)
                        }}
                        className="block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 dark:file:bg-indigo-900/30 file:text-indigo-700 dark:file:text-indigo-400 hover:file:bg-indigo-100 dark:hover:file:bg-indigo-900/50"
                      />
                      {file.content && (
                        <p className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                          Uploaded: {file.filename} ({file.content.length} chars)
                        </p>
                      )}
                    </div>
                  )}

                  {file.mode === 'write' && (
                    <div className="space-y-2">
                      <input
                        type="text"
                        value={file.filename || ''}
                        onChange={(e) => handleFilenameChange(file.id, e.target.value)}
                        placeholder={`filename${getFileExtension()}`}
                        className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-3 py-2 text-sm"
                      />
                      <textarea
                        value={file.content || ''}
                        onChange={(e) => handleContentChange(file.id, e.target.value)}
                        placeholder="Enter file content..."
                        rows={6}
                        className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-3 py-2 text-sm font-mono"
                      />
                    </div>
                  )}
                </>
              )}
            </div>
          )
        })}
      </div>

      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={handleAddFile}
          disabled={maxFiles ? files.length >= maxFiles : false}
          className="text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 disabled:text-gray-400 disabled:cursor-not-allowed"
        >
          + Add Another File
        </button>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          {completeFiles} / {files.length} files complete
          {minFiles > 1 && !hasMinimumFiles && (
            <span className="text-red-500 ml-2">(need at least {minFiles})</span>
          )}
        </div>
      </div>

      {showValidation && (
        <p className="text-sm text-red-600 dark:text-red-400">
          Please complete at least {minFiles} file{minFiles > 1 ? 's' : ''}
        </p>
      )}
    </div>
  )
}
