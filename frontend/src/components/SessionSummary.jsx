import LatexContent from './LatexContent.jsx'

const ASSESSMENT_ICON = {
  correct: { icon: '✓', color: 'text-green-600', bg: 'bg-green-50' },
  partial: { icon: '~', color: 'text-amber-600', bg: 'bg-amber-50' },
  wrong: { icon: '✗', color: 'text-red-500', bg: 'bg-red-50' },
}

export default function SessionSummary({ type, topicName, results, onTryAgain, onHome }) {
  if (type === 'extended') {
    const correct = results.filter(r => r.assessment === 'correct').length
    const total = results.length

    return (
      <div className="min-h-screen bg-white">
        <div className="max-w-3xl mx-auto px-6 py-10">
          <div className="mb-8 text-center">
            <p className="text-slate-400 text-sm mb-1">Session complete</p>
            <h1 className="text-2xl font-semibold text-slate-800">{topicName}</h1>
          </div>

          <div className="border border-slate-200 rounded-xl p-6 mb-6 text-center">
            <p className="text-slate-500 text-sm mb-1">You rated yourself</p>
            <p className="text-3xl font-semibold text-teal-700">{correct} / {total}</p>
            <p className="text-slate-400 text-sm mt-1">correct</p>
          </div>

          <div className="border border-slate-200 rounded-xl divide-y divide-slate-100 mb-8">
            {results.map((r, i) => {
              const style = ASSESSMENT_ICON[r.assessment]
              return (
                <div key={i} className="flex items-start gap-3 px-5 py-4">
                  <span className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0 ${style.color} ${style.bg}`}>
                    {style.icon}
                  </span>
                  <div>
                    <span className="font-medium text-slate-700 text-sm">{r.displayLabel}</span>
                    <p className="text-slate-400 text-xs mt-0.5">{r.curriculum_tag}</p>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={onTryAgain}
              className="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-medium py-2.5 rounded-lg transition-colors"
            >
              Try another session
            </button>
            <button
              onClick={onHome}
              className="flex-1 border border-slate-200 text-slate-600 hover:bg-slate-50 font-medium py-2.5 rounded-lg transition-colors"
            >
              Back to home
            </button>
          </div>
        </div>
      </div>
    )
  }

  // MCQ summary
  const { score, total, results: mcqResults } = results

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-6 py-10">
        <div className="mb-8 text-center">
          <p className="text-slate-400 text-sm mb-1">Session complete</p>
          <h1 className="text-2xl font-semibold text-slate-800">{topicName}</h1>
        </div>

        <div className="border border-slate-200 rounded-xl p-6 mb-6 text-center">
          <p className="text-slate-500 text-sm mb-1">Your score</p>
          <p className="text-3xl font-semibold text-teal-700">{score} / {total}</p>
        </div>

        <div className="border border-slate-200 rounded-xl divide-y divide-slate-100 mb-8">
          {mcqResults.map((r, i) => {
            const isCorrect = r.correct
            return (
              <div key={i} className="px-5 py-4">
                <div className="flex items-start gap-3 mb-2">
                  <span className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0 ${
                    isCorrect
                      ? 'text-green-600 bg-green-50'
                      : 'text-red-500 bg-red-50'
                  }`}>
                    {isCorrect ? '✓' : '✗'}
                  </span>
                  <div className="text-sm text-slate-600">
                    <span className="font-medium">Q{i + 1}</span>
                    {' '}
                    <span className="text-slate-400">
                      Your answer: <strong className={isCorrect ? 'text-green-600' : 'text-red-500'}>{r.student_answer || '—'}</strong>
                      {!isCorrect && (
                        <> · Correct: <strong className="text-green-600">{r.correct_answer}</strong></>
                      )}
                    </span>
                  </div>
                </div>
                <div className="ml-10 text-xs text-slate-500 leading-relaxed">
                  <LatexContent content={r.explanation_latex} />
                </div>
              </div>
            )
          })}
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={onTryAgain}
            className="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-medium py-2.5 rounded-lg transition-colors"
          >
            Try another session
          </button>
          <button
            onClick={onHome}
            className="flex-1 border border-slate-200 text-slate-600 hover:bg-slate-50 font-medium py-2.5 rounded-lg transition-colors"
          >
            Back to home
          </button>
        </div>
      </div>
    </div>
  )
}
