import { useEffect, useRef } from 'react'

export default function LatexContent({ content, className = '' }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!ref.current) return
    const timeout = setTimeout(() => {
      if (window.renderMathInElement) {
        window.renderMathInElement(ref.current, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false },
          ],
          throwOnError: false,
        })
      }
    }, 50)
    return () => clearTimeout(timeout)
  }, [content])

  return (
    <div
      ref={ref}
      className={className}
      dangerouslySetInnerHTML={{ __html: content }}
    />
  )
}
