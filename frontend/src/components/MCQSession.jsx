import { useState } from 'react'
import LatexContent from './LatexContent.jsx'
import Spinner from './Spinner.jsx'

export default function MCQSession({ session, onDone, onHome }) {
  const questions = session.questions
  const [qIdx, setQIdx] = useState(0)
  const [answers, setAnswers] = useState({}) // index → 'A'|'B'|'C'|'D'
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const q = questions[qIdx]
  const selected = answers[qIdx]

  function handleSelect(letter) {
    setAnswers(prev => ({ ...prev, [qIdx]: letter }))
  }

  async function handleNext() {
    if (qIdx + 1 < questions.length) {
      setQIdx(qIdx + 1)
      return
    }

    // Last question — submit
    setSubmitting(true)
    setError(null)
    try {
      const orderedAnswers = questions.map((_, i) => answers[i] || '')
      const res = await fetch('/api/mcq/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session.session_id,
          answers: orderedAnswers,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'submit_failed')
      }
      const data = await res.json()
      onDone(data)
    } catch (e) {
      setError(e.message.includes('expired')
        ? 'Session expired. Please start a new session.'
        : 'Could not submit. Please try again.')
      setSubmitting(false)
    }
  }

  if (submitting) return <Spinner fullPage />

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
            <p className="text-slate-400 text-sm">Multiple Choice</p>
          </div>
          <div className="text-sm text-slate-500 font-medium">
            Question {qIdx + 1} of {questions.length}
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-slate-100 rounded-full h-1 mb-8">
          <div
            className="bg-teal-500 h-1 rounded-full transition-all"
            style={{ width: `${((qIdx + 1) / questions.length) * 100}%` }}
          />
        </div>

        {/* Question card */}
        <div className="border border-slate-200 rounded-xl p-6 mb-6">
          <div className="text-slate-800 text-base leading-relaxed mb-6">
            <LatexContent content={q.question_latex} />
          </div>

          <div className="flex flex-col gap-2">
            {['A', 'B', 'C', 'D'].map(letter => (
              <button
                key={letter}
                onClick={() => handleSelect(letter)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg border text-left transition-colors ${
                  selected === letter
                    ? 'border-teal-500 bg-teal-50 text-teal-800'
                    : 'border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                }`}
              >
                <span className={`w-7 h-7 rounded-full border-2 flex items-center justify-center text-sm font-semibold flex-shrink-0 ${
                  selected === letter
                    ? 'border-teal-500 bg-teal-500 text-white'
                    : 'border-slate-300 text-slate-500'
                }`}>
                  {letter}
                </span>
                <LatexContent content={q.options[letter]} className="flex-1" />
              </button>
            ))}
          </div>
        </div>

        {error && <p className="text-red-600 text-sm mb-4 text-center">{error}</p>}

        <button
          onClick={handleNext}
          disabled={!selected}
          className="w-full bg-teal-600 hover:bg-teal-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg transition-colors"
        >
          {qIdx + 1 >= questions.length ? 'Submit answers' : 'Next question →'}
        </button>
      </div>
    </div>
  )
}
