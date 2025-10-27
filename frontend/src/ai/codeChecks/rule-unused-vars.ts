import { parse } from '@babel/parser'
import type { ParserOptions, ParserPlugin } from '@babel/parser'
import type { Issue } from './index'

const parserPlugins: ParserPlugin[] = ['jsx', 'typescript']

const parserOptions: ParserOptions = {
  sourceType: 'module',
  plugins: parserPlugins,
  errorRecovery: true,
}

type DeclarationMeta = {
  used: boolean
  location?: { line: number; column: number }
}

export function checkUnusedVars(code: string): Issue[] {
  const ast = parse(code, parserOptions)
  const declarations = new Map<string, DeclarationMeta>()

  function visit(node: any, parent?: any, parentKey?: string) {
    if (!node || typeof node !== 'object') return

    if (node.type === 'VariableDeclarator' && node.id?.type === 'Identifier') {
      const name = node.id.name
      if (!declarations.has(name)) {
        declarations.set(name, {
          used: false,
          location: node.loc?.start
            ? { line: node.loc.start.line, column: node.loc.start.column }
            : undefined,
        })
      }
    }

    if (node.type === 'Identifier') {
      const isDeclarationIdentifier =
        parent &&
        ((parent.type === 'VariableDeclarator' && parentKey === 'id') ||
          ((parent.type === 'FunctionDeclaration' || parent.type === 'FunctionExpression') && parentKey === 'id') ||
          (parent.type === 'ClassDeclaration' && parentKey === 'id') ||
          (parent.type === 'CatchClause' && parentKey === 'param'))

      if (!isDeclarationIdentifier && declarations.has(node.name)) {
        const meta = declarations.get(node.name)
        if (meta) meta.used = true
      }
    }

    for (const key of Object.keys(node)) {
      const child = (node as any)[key]
      if (Array.isArray(child)) child.forEach((item) => visit(item, node, key))
      else visit(child, node, key)
    }
  }

  visit(ast.program)

  const issues: Issue[] = []
  for (const [name, meta] of declarations.entries()) {
    if (!meta.used) {
      issues.push({
        rule: 'unused-vars',
        message: `Variable "${name}" is declared but never used.`,
        severity: 'warn',
        fixHint: `Remove "${name}" or use it.`,
        location: meta.location,
      })
    }
  }

  return issues
}
