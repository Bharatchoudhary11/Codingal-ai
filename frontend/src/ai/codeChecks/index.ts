import { checkDuplicateBlocks } from './rule-duplicate-block'
import { checkForLoopOffByOne } from './rule-for-loop-off-by-one'
import { checkMissingReturn } from './rule-missing-return'
import { checkUnusedVars } from './rule-unused-vars'

export type Issue = {
  rule: string
  message: string
  nodeType?: string
  severity: 'info' | 'warn' | 'error'
  fixHint?: string
  location?: { line: number; column: number }
}

export function analyze(code: string): Issue[] {
  return [
    ...checkUnusedVars(code),
    ...checkForLoopOffByOne(code),
    ...checkMissingReturn(code),
    ...checkDuplicateBlocks(code),
  ]
}
