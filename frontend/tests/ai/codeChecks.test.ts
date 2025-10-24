import { describe, expect, it } from 'vitest'
import { analyze } from '../../src/ai/codeChecks'

describe('code checks', () => {
  it('flags unused variables', () => {
    const code = 'const unusedValue = 1; console.log("hi")'
    const issues = analyze(code)
    expect(issues.some((issue) => issue.rule === 'unused-vars')).toBe(true)
  })

  it('detects <= usage in array length loops', () => {
    const code = 'for (let i = 0; i <= items.length; i++) { console.log(items[i]); }'
    const issues = analyze(code)
    expect(issues.some((issue) => issue.rule === 'for-loop-off-by-one')).toBe(true)
  })

  it('warns about missing return statements', () => {
    const code = `
      function calculateTotal(values) {
        let total = 0;
        for (const value of values) {
          total += value;
        }
      }
    `
    const issues = analyze(code)
    expect(issues.some((issue) => issue.rule === 'missing-return')).toBe(true)
  })

  it('identifies duplicate blocks', () => {
    const code = `
      function handle(flag) {
        if (flag) {
          console.log('repeat');
        } else {
          console.log('repeat');
        }
      }
    `
    const issues = analyze(code)
    expect(issues.some((issue) => issue.rule === 'duplicate-block')).toBe(true)
  })

  it('passes clean snippets without findings', () => {
    const code = `
      const numbers = [1, 2, 3];
      const doubled = numbers.map((value) => value * 2);
      export function sum(values) {
        return values.reduce((accumulator, value) => accumulator + value, 0);
      }
    `
    const issues = analyze(code)
    expect(issues).toHaveLength(0)
  })
})
