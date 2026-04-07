import { useState, useEffect } from 'react'

const MESSAGES = [
  'Generating your question...',
  'Checking curriculum alignment...',
  'Preparing hints...',
]

export default function Spinner({ fullPage = false }) {
  const [msgIdx, setMsgIdx] = useState(0)

  useEffect(() => {
    if (!fullPage) return
    const interval = setInterval(() => {
      setMsgIdx(i => (i + 1) % MESSAGES.length)
    }, 1800)
    return () => clearInterval(interval)
  }, [fullPage])

  if (fullPage) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-4">
        <div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-500 text-sm">{MESSAGES[msgIdx]}</p>
      </div>
    )
  }

  return (
    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
  )
}
