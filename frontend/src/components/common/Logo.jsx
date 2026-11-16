export default function Logo({ size = 'medium' }) {
  const sizes = {
    small: 'text-2xl',
    medium: 'text-4xl',
    large: 'text-6xl',
  }

  return (
    <div className="flex items-center justify-center gap-2">
      <span className={sizes[size]}>🥡</span>
      <span className={`font-display font-extrabold ${sizes[size]} text-dark`}>
        Hong<span className="text-brand-500">Kong</span>
      </span>
    </div>
  )
}