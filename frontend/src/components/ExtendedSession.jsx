import { useState } from 'react'
import LatexContent from './LatexContent.jsx'

export default function ExtendedSession({ session, onDone, onHome }) {
  // Flatten all parts from all questions into a single list
  const allParts = session.questions.flatMap(q =>
    q.parts.map(p => ({
      ...p,
      questionIndex: q.index,
      displayLabel: `Q${q.index + 1}${p.label}`,
    }))
  )

  const [partIdx, setPartIdx] = useState(0)
  const [solutionVisible, setSolutionVisible] = useState(false)
  const [solutionLatex, setSolutionLatex] = useState(null)
  const [solutionLoading, setSolutionLoading] = useState(false)
  const [solutionError, setSolutionError] = useState(null)
  const [assessment, setAssessment] = useState(null) // 'correct' | 'partial' | 'wrong'
  const [completedParts, setCompletedParts] = useState([])

  const part = allParts[partIdx]

  async function handleShowSolution() {
    setSolutionLoading(true)
    setSolutionError(null)
    try {
      const res = await fetch('/api/extended/solution', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session.session_id,
          question_index: part.questionIndex,
          part_label: part.label,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'failed')
      }
      const data = await res.json()
      setSolutionLatex(data.worked_solution_latex)
      setSolutionVisible(true)
    } catch (e) {
      setSolutionError(e.message.includes('expired')
        ? 'Session expired. Please start a new session.'
        : 'Could not load solution. Please try again.')
    } finally {
      setSolutionLoading(false)
    }
  }

  function handleNext() {
    const done = [
      ...completedParts,
      {
        displayLabel: part.displayLabel,
        curriculum_tag: part.curriculum_tag,
        assessment,
      },
    ]

    if (partIdx + 1 >= allParts.length) {
      onDone(done)
    } else {
      setCompletedParts(done)
      setPartIdx(partIdx + 1)
      setSolutionVisible(false)
      setSolutionLatex(null)
      setSolutionError(null)
      setAssessment(null)
    }
  }

  const assessmentOptions = [
    { value: 'wrong', label: '✗ Wrong', color: 'border-red-400 bg-red-50 text-red-700' },
    { value: 'partial', label: '~ Partial', color: 'border-amber-400 bg-amber-50 text-amber-700' },
    { value: 'correct', label: '✓ Correct', color: 'border-green-400 bg-green-50 text-green-700' },
  ]

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button onClick={onHome} className="text-slate-400 hover:text-slate-600 text-sm">
            ← Home
          </button>
          <div className="text-center">
            <h1 className="text-xl font-semibold text-slate-800">{session.topic_name}</h1>
            <p className="text-slate-400 text-sm">Extended Response</p>
          </div>
          <div className="text-sm text-slate-400">
            {partIdx + 1} / {allParts.length}
          </div>
        </div>

        {/* Question card */}
        <div className="border border-slate-200 rounded-xl p-6 mb-4">
          {/* Part header */}
          <div className="flex items-start justify-between gap-4 mb-4">
            <span className="font-semibold text-teal-700 text-sm bg-teal-50 px-3 py-1 rounded-full">
              {part.displayLabel} — {part.marks} {part.marks === 1 ? 'mark' : 'marks'}
            </span>
            <span className="text-xs text-slate-400 text-right leading-tight max-w-xs">
              {part.curriculum_tag}
            </span>
          </div>

          {/* Question */}
          <div className="text-slate-800 text-base mb-6 leading-relaxed">
            <LatexContent content={part.question_latex} />
          </div>

          {/* Formula reference */}
          <div className="bg-slate-50 rounded-lg p-4 mb-6">
            <p className="text-xs text-slate-400 font-medium mb-2">
              <span className="mr-1">📐</span>Formula
            </p>
            <LatexContent content={part.formula_reference} />
          </div>

          {/* Show worked solution */}
          {!solutionVisible && (
            <div className="mb-6">
              <button
                onClick={handleShowSolution}
                disabled={solutionLoading}
                className="w-full py-2.5 border border-slate-300 rounded-lg text-slate-600 text-sm font-medium hover:bg-slate-50 disabled:opacity-50 transition-colors"
              >
                {solutionLoading ? 'Loading...' : 'Show worked solution'}
              </button>
              {solutionError && (
                <p className="text-red-600 text-xs mt-2 text-center">{solutionError}</p>
              )}
            </div>
          )}

          {/* Worked solution */}
          {solutionVisible && solutionLatex && (
            <div className="mb-6">
              <div className="border-t border-slate-200 pt-4">
                <p className="text-xs text-slate-400 uppercase tracking-wider mb-3">Worked solution</p>
                <div className="text-slate-700 text-sm leading-relaxed">
                  <LatexContent content={solutionLatex} />
                </div>
              </div>
            </div>
          )}

          {/* Self assessment */}
          <div>
            <p className="text-sm text-slate-600 mb-2 font-medium">How did you go?</p>
            <div className="flex gap-2">
              {assessmentOptions.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setAssessment(opt.value)}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-colors ${
                    assessment === opt.value
                      ? opt.color
                      : 'border-slate-200 text-slate-500 hover:border-slate-300'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Next button */}
        {assessment && (
          <button
            onClick={handleNext}
            className="w-full bg-teal-600 hover:bg-teal-700 text-white font-medium py-3 rounded-lg transition-colors"
          >
            {partIdx + 1 >= allParts.length ? 'Finish session' : 'Next part →'}
          </button>
        )}
      </div>
    </div>
  )
}
