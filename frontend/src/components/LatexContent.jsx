import { useEffect, useRef } from 'react'

export default function LatexContent({ content, className = '' }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!ref.current || !content) return
    // Set as plain text so HTML special chars in LaTeX (< > &) are not interpreted as markup
    ref.current.textContent = content
    if (window.renderMathInElement) {
      window.renderMathInElement(ref.current, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\[', right: '\\]', display: true },
          { left: '\\(', right: '\\)', display: false },
        ],
        throwOnError: false,
      })
    }
  }, [content])

  return <div ref={ref} className={className} />
}
