import type { Recommendation } from '../ai/recommender'

type Props = {
  recommendation: Recommendation | null
  explanation: string
}

export default function CoachPanel({ recommendation, explanation }: Props) {
  if (!recommendation) {
    return (
      <section className="rounded-2xl border bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">AI Course Coach</h2>
        <p className="mt-2 text-sm text-gray-600">Loading recommendation…</p>
      </section>
    )
  }

  const featureEntries = Object.entries(recommendation.reasonFeatures)

  return (
    <section className="rounded-2xl border bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h2 className="text-lg font-semibold">AI Course Coach</h2>
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
          Confidence {Math.round(recommendation.confidence * 100)}%
        </span>
      </div>
      <p className="mt-2 text-sm text-gray-700">
        Deterministic heuristic using progress gaps, recency, tag mastery, hint usage, and recent correctness.
      </p>
      <div className="mt-4 rounded-xl bg-gray-50 p-4 text-sm text-gray-800">
        <p className="font-medium text-gray-900">{recommendation.title}</p>
        <ul className="mt-3 space-y-1 text-xs text-gray-600">
          {featureEntries.map(([key, value]) => (
            <li key={key}>
              <span className="font-medium text-gray-700">{key.replace(/_/g, ' ')}:</span> {value}
            </li>
          ))}
        </ul>
      </div>
      {recommendation.alternatives.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-semibold text-gray-800">Alternative picks</h3>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-xs text-gray-600">
            {recommendation.alternatives.map((option) => (
              <li key={option.id}>
                {option.title}
                <span className="ml-1 text-[11px] text-gray-400">({option.reason})</span>
              </li>
            ))}
          </ol>
        </div>
      )}
      <details className="mt-4 rounded-xl border border-dashed border-gray-200 bg-gray-50 p-3 text-xs text-gray-600">
        <summary className="cursor-pointer select-none font-medium text-gray-700">How it works</summary>
        <pre className="mt-2 whitespace-pre-wrap text-[11px] leading-relaxed">{explanation}</pre>
      </details>
    </section>
  )
}
