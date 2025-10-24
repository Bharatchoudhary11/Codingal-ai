import { parse } from '@babel/parser'

import type { Issue } from './index'

const parserOptions = {
  sourceType: 'module' as const,
  plugins: ['jsx', 'typescript'] as const,
  errorRecovery: true,
}

function isLengthMember(node: any) {
  return (
    node &&
    node.type === 'MemberExpression' &&
    !node.computed &&
    node.property?.type === 'Identifier' &&
    node.property.name === 'length'
  )
}

export function checkForLoopOffByOne(code: string): Issue[] {
  const ast = parse(code, parserOptions)
  const issues: Issue[] = []

  function visit(node: any) {
    if (!node || typeof node !== 'object') return

    if (node.type === 'ForStatement' && node.test?.type === 'BinaryExpression') {
      const test = node.test
      if (
        test.operator === '<=' &&
        (isLengthMember(test.right) || (test.right?.type === 'BinaryExpression' && isLengthMember(test.right.left)))
      ) {
        issues.push({
          rule: 'for-loop-off-by-one',
          message: 'Potential off-by-one: prefer "<" when comparing against array.length.',
          severity: 'info',
          fixHint: 'Change "<=" to "<" to avoid reading past the end of the array.',
          location: test.loc?.start
            ? { line: test.loc.start.line, column: test.loc.start.column }
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
