import { parse } from '@babel/parser'
import type { ParserOptions, ParserPlugin } from '@babel/parser'
import type { Issue } from './index'

const parserPlugins: ParserPlugin[] = ['jsx', 'typescript']

const parserOptions: ParserOptions = {
  sourceType: 'module',
  plugins: parserPlugins,
  errorRecovery: true,
}

export function checkDuplicateBlocks(code: string): Issue[] {
  const ast = parse(code, parserOptions)
  const issues: Issue[] = []
  const seen = new Map<string, { count: number; loc?: { line: number; column: number } }>()

  function normalizeSnippet(snippet: string) {
    return snippet
      .replace(/[{}\s]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
  }

  function visit(node: any) {
    if (!node || typeof node !== 'object') return

    if (node.type === 'BlockStatement') {
      const raw =
        typeof node.start === 'number' && typeof node.end === 'number'
          ? code.slice(node.start, node.end)
          : JSON.stringify(node.body)
      const snippet = normalizeSnippet(raw)
      if (snippet && snippet !== '{}' && snippet.length > 3) {
        const key = snippet
        const location =
          node.loc && node.loc.start ? { line: node.loc.start.line, column: node.loc.start.column } : undefined
        if (seen.has(key)) {
          const previous = seen.get(key)
          if (previous && previous.count === 1) {
            issues.push({
              rule: 'duplicate-block',
              message: 'Duplicate block detected. Consider extracting a helper to avoid repetition.',
              severity: 'info',
              fixHint: 'Extract the shared statements into a function and reuse it.',
              location,
            })
          }
          seen.set(key, { count: previous!.count + 1, loc: previous!.loc })
        } else {
          seen.set(key, { count: 1, loc: location })
        }
      }
    }

    for (const key of Object.keys(node)) {
      const child = (node as any)[key]
      if (Array.isArray(child)) child.forEach(visit)
      else visit(child)
    }
  }

  visit(ast.program)
  return issues
}
