import { parse } from '@babel/parser'
import type { ParserOptions, ParserPlugin } from '@babel/parser'
import type { Issue } from './index'

const parserPlugins: ParserPlugin[] = ['jsx', 'typescript']

const parserOptions: ParserOptions = {
  sourceType: 'module',
  plugins: parserPlugins,
  errorRecovery: true,
}

export function checkMissingReturn(code: string): Issue[] {
  const ast = parse(code, parserOptions)
  const issues: Issue[] = []

  function containsReturn(node: any): boolean {
    if (!node || typeof node !== 'object') return false
    if (node.type === 'ReturnStatement') return true
    for (const key of Object.keys(node)) {
      const child = (node as any)[key]
      if (Array.isArray(child)) {
        if (child.some(containsReturn)) return true
      } else if (containsReturn(child)) {
        return true
      }
    }
    return false
  }

  function visit(node: any) {
    if (!node || typeof node !== 'object') return

    if (
      (node.type === 'FunctionDeclaration' ||
        node.type === 'FunctionExpression' ||
        node.type === 'ArrowFunctionExpression') &&
      node.body &&
      node.body.type === 'BlockStatement'
    ) {
      const hasReturn = containsReturn(node.body)
      if (!hasReturn) {
        const name = node.id?.name || (node.type === 'FunctionExpression' && node.id?.name) || 'anonymous function'
        issues.push({
          rule: 'missing-return',
          message: `Function "${name}" does not return a value. Return the computed result or clarify intent.`,
          severity: 'warn',
          fixHint: 'Ensure every path returns a value (or convert to a void-style helper).',
          location: node.loc?.start
            ? { line: node.loc.start.line, column: node.loc.start.column }
            : undefined,
        })
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
