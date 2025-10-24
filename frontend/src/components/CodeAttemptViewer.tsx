import type { Issue } from '../ai/codeChecks'

type Props = {
  code: string
  onChange: (value: string) => void
  onAnalyze: () => void
  issues: Issue[]
  hasAnalyzed: boolean
}

export default function CodeAttemptViewer({ code, onChange, onAnalyze, issues, hasAnalyzed }: Props) {
  return (
    <div className="rounded-2xl border bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-gray-800">Code Attempt Viewer</h3>
        <button
          className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-800"
          onClick={onAnalyze}
        >
          Run checks
        </button>
      </div>
      <p className="mt-1 text-xs text-gray-500">
        Runs deterministic AST rules (unused vars, off-by-one loops, missing return, duplicate blocks).
      </p>
      <textarea
        className="mt-3 h-40 w-full rounded-xl border border-gray-200 bg-gray-50 p-3 font-mono text-xs text-gray-800 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
        value={code}
        onChange={(event) => onChange(event.target.value)}
        spellCheck={false}
      />
      <div className="mt-3 rounded-xl bg-gray-50 p-3 text-xs">
        {!hasAnalyzed && <p className="text-gray-500">No analysis yet. Modify the code and run the checks.</p>}
        {hasAnalyzed && issues.length === 0 && (
          <p className="font-medium text-emerald-600">No issues found. Great job!</p>
        )}
        {issues.length > 0 && (
          <ul className="space-y-2">
            {issues.map((issue, index) => (
              <li key={`${issue.rule}-${index}`} className="rounded-lg bg-white p-2 shadow-sm">
                <p className="font-semibold text-gray-800">{issue.rule}</p>
                <p className="text-gray-600">{issue.message}</p>
                {issue.location && (
                  <p className="text-[11px] text-gray-400">
                    Line {issue.location.line}, column {issue.location.column}
                  </p>
                )}
                {issue.fixHint && <p className="text-[11px] text-indigo-500">Hint: {issue.fixHint}</p>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
