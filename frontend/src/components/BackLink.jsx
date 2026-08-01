export default function BackLink({ onClick, label = 'Back' }) {
  return (
    <button
      onClick={onClick}
      className="text-sm text-soft hover:text-ink mb-6 inline-flex items-center gap-1.5"
    >
      <span aria-hidden="true">←</span> {label}
    </button>
  )
}
