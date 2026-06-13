export default function FormattedText({ text, className = '', tag: Tag = 'div' }) {
  if (!text) return null
  return <Tag className={`formatted-text ${className}`.trim()}>{text}</Tag>
}
