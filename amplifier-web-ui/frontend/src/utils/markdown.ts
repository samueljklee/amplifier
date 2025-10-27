export function simpleMarkdownToHtml(markdown: string | undefined | null): string {
  // Handle undefined/null markdown
  if (!markdown) {
    return '<p class="text-gray-500 italic">No content available</p>'
  }

  const escapeHtml = (text: string) =>
    text.replace(/[<>&"']/g, (char) => {
      const entities: Record<string, string> = {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;',
        '"': '&quot;',
        "'": '&#39;'
      }
      return entities[char]
    })

  const lines = markdown.split('\n')
  const htmlLines: string[] = []
  let inCodeBlock = false
  let codeBlockContent: string[] = []

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i]

    if (line.startsWith('```')) {
      if (inCodeBlock) {
        htmlLines.push(`<pre class="bg-gray-800 dark:bg-gray-950 text-gray-100 p-4 rounded-lg overflow-x-auto my-4"><code>${codeBlockContent.join('\n')}</code></pre>`)
        codeBlockContent = []
        inCodeBlock = false
      } else {
        inCodeBlock = true
      }
      continue
    }

    if (inCodeBlock) {
      codeBlockContent.push(escapeHtml(line))
      continue
    }

    if (line.startsWith('### ')) {
      htmlLines.push(`<h3 class="text-lg font-bold mt-6 mb-3 text-gray-900 dark:text-gray-100">${escapeHtml(line.substring(4))}</h3>`)
    } else if (line.startsWith('## ')) {
      htmlLines.push(`<h2 class="text-xl font-bold mt-8 mb-4 text-gray-900 dark:text-gray-100">${escapeHtml(line.substring(3))}</h2>`)
    } else if (line.startsWith('# ')) {
      htmlLines.push(`<h1 class="text-2xl font-bold mt-10 mb-5 text-gray-900 dark:text-gray-100">${escapeHtml(line.substring(2))}</h1>`)
    }
    else if (line.match(/^[\*\-] /)) {
      const content = escapeHtml(line.substring(2))
      htmlLines.push(`<li class="ml-6 mb-2 text-gray-800 dark:text-gray-200">• ${processInlineMarkdown(content)}</li>`)
    }
    else if (line.startsWith('> ')) {
      htmlLines.push(`<blockquote class="border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic my-4 text-gray-700 dark:text-gray-300">${processInlineMarkdown(escapeHtml(line.substring(2)))}</blockquote>`)
    }
    else if (line.match(/^---+$/)) {
      htmlLines.push('<hr class="my-6 border-gray-300 dark:border-gray-600" />')
    }
    else if (line.trim() === '') {
      htmlLines.push('<div class="h-4"></div>')
    }
    else {
      htmlLines.push(`<p class="mb-4 text-gray-800 dark:text-gray-200 leading-relaxed">${processInlineMarkdown(escapeHtml(line))}</p>`)
    }
  }

  return `<div class="markdown-preview">${htmlLines.join('\n')}</div>`
}

export function processInlineMarkdown(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong class="font-bold">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em class="italic">$1</em>')
    .replace(/\[(.+?)\]\((.+?)\)/g, (match, linkText, url) => {
      const unescapedUrl = url.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
      return `<a href="${unescapedUrl}" class="text-indigo-600 dark:text-indigo-400 hover:underline" target="_blank" rel="noopener noreferrer">${linkText}</a>`
    })
    .replace(/`(.+?)`/g, '<code class="bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded text-sm font-mono">$1</code>')
}
