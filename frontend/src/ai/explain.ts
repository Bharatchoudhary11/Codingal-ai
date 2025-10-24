import type { Recommendation } from './recommender'

export function formatExplanation(rec: Recommendation) {
  const lines = [
    `Recommendation: ${rec.title}`,
    `Method: ${rec.method}`,
    `Confidence: ${rec.confidence.toFixed(2)}`,
    'Reasoning features:',
    ...Object.entries(rec.reasonFeatures).map(([key, value]) => `  - ${key}: ${value}`),
    ...(rec.alternatives?.length
      ? [
          'Alternatives:',
          ...rec.alternatives.map((option, index) => `  ${index + 1}. ${option.title} — ${option.reason}`),
        ]
      : []),
    'Limitations: Simple heuristic baseline. Replace with richer features or a local model when available.',
  ]

  return lines.join('\n')
}
