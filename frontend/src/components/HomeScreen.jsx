import { useState } from 'react'
import Spinner from './Spinner.jsx'

const EXTENDED_TOPICS = [
  { label: 'Implicit Differentiation', code: 'SM_AOS4_T1' },
  { label: 'Integration Techniques', code: 'SM_AOS4_T2' },
  { label: 'Differential Equations', code: 'SM_AOS4_T3' },
  { label: 'Kinematics', code: 'SM_AOS4_T4' },
  { label: 'Complex Numbers', code: 'SM_AOS3_T1' },
  { label: 'Complex Loci', code: 'SM_AOS3_T2' },
  { label: 'Vectors (3D)', code: 'SM_AOS5_T1' },
  { label: 'Lines and Planes', code: 'SM_AOS5_T2' },
  { label: 'Logic and Proof', code: 'SM_AOS1_T2' },
  { label: 'Mathematical Induction', code: 'SM_AOS1_T3' },
  { label: 'Rational Functions', code: 'SM_AOS2_T1' },
  { label: 'Statistics', code: 'SM_AOS6_T3' },
  { label: 'Hypothesis Testing', code: 'SM_AOS6_T4' },
  { label: 'PDF and Sampling', code: 'SM_AOS6_T5' },
]

const MCQ_TOPICS = [
  { label: 'Logic and Proof', code: 'SM_AOS1_T1' },
  { label: 'Complex Numbers', code: 'SM_AOS3_T1' },
  { label: 'Integration', code: 'SM_AOS4_T2' },
  { label: 'Differential Equations', code: 'SM_AOS4_T3' },
  { label: 'Kinematics', code: 'SM_AOS4_T4' },
  { label: 'Vectors', code: 'SM_AOS5_T1' },
  { label: 'Lines and Planes', code: 'SM_AOS5_T2' },
  { label: 'Statistics', code: 'SM_AOS6_T1' },
]

export default function HomeScreen({ onExtendedStart, onMcqStart }) {
  const [extTopic, setExtTopic] = useState(EXTENDED_TOPICS[0].code)
  const [difficulty, setDifficulty] = useState('standard')
  const [mcqTopic, setMcqTopic] = useState(MCQ_TOPICS[0].code)
  const [extLoading, setExtLoading] = useState(false)
  const [mcqLoading, setMcqLoading] = useState(false)
  const [extError, setExtError] = useState(null)
  const [mcqError, setMcqError] = useState(null)

  async function handleExtendedGenerate() {
    setExtLoading(true)
    setExtError(null)
    try {
      const res = await fetch('/api/extended/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic_code: extTopic, difficulty }),
      })
      if (!res.ok) throw new Error('generation_failed')
      const data = await res.json()
      onExtendedStart(data)
    } catch {
      setExtError('Could not generate questions. Please try again.')
    } finally {
      setExtLoading(false)
    }
  }

  async function handleMcqGenerate() {
    setMcqLoading(true)
    setMcqError(null)
    try {
      const res = await fetch('/api/mcq/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic_code: mcqTopic }),
      })
      if (!res.ok) throw new Error('generation_failed')
      const data = await res.json()
      onMcqStart(data)
    } catch {
      setMcqError('Could not generate questions. Please try again.')
    } finally {
      setMcqLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-semibold text-slate-800 tracking-tight mb-2">GenSheet VCE</h1>
          <p className="text-slate-500 text-lg">Specialist Mathematics exam practice · Year 12</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Extended Response Card */}
          <div className="border border-slate-200 rounded-xl p-6 flex flex-col gap-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-800">Extended Response</h2>
              <p className="text-slate-500 text-sm mt-1">Multi-part questions — Exam 1 style</p>
            </div>

            <div className="flex flex-col gap-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Topic</label>
                <select
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  value={extTopic}
                  onChange={e => setExtTopic(e.target.value)}
                >
                  {EXTENDED_TOPICS.map(t => (
                    <option key={t.code} value={t.code}>{t.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Difficulty</label>
                <div className="flex gap-2">
                  {['standard', 'hard'].map(d => (
                    <button
                      key={d}
                      onClick={() => setDifficulty(d)}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-colors ${
                        difficulty === d
                          ? 'bg-teal-600 text-white border-teal-600'
                          : 'bg-white text-slate-600 border-slate-200 hover:border-teal-400'
                      }`}
                    >
                      {d.charAt(0).toUpperCase() + d.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {extError && (
              <p className="text-red-600 text-sm">{extError}</p>
            )}

            <button
              onClick={handleExtendedGenerate}
              disabled={extLoading}
              className="mt-auto w-full bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {extLoading ? <Spinner /> : 'Generate Questions →'}
            </button>
          </div>

          {/* MCQ Card */}
          <div className="border border-slate-200 rounded-xl p-6 flex flex-col gap-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-800">Multiple Choice</h2>
              <p className="text-slate-500 text-sm mt-1">5 questions — Exam 2 Section A style</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Topic</label>
              <select
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                value={mcqTopic}
                onChange={e => setMcqTopic(e.target.value)}
              >
                {MCQ_TOPICS.map(t => (
                  <option key={t.code} value={t.code}>{t.label}</option>
                ))}
              </select>
            </div>

            {mcqError && (
              <p className="text-red-600 text-sm">{mcqError}</p>
            )}

            <button
              onClick={handleMcqGenerate}
              disabled={mcqLoading}
              className="mt-auto w-full bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {mcqLoading ? <Spinner /> : 'Generate Questions →'}
            </button>
          </div>
        </div>

        <p className="text-center text-slate-400 text-xs mt-10">
          No login required. GenSheet VCE · Part of the GenSheet suite
        </p>
      </div>
    </div>
  )
}
