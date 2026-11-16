import { Search, X } from 'lucide-react'

export default function SearchBar({ value, onChange, placeholder = 'Search restaurants...' }) {
  return (
    <div className="relative">
      <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-12 pr-10 py-3 bg-white border-2 border-gray-100 rounded-2xl focus:border-brand-500 focus:ring-2 focus:ring-brand-200 outline-none transition-all shadow-card"
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-4 top-1/2 -translate-y-1/2 text-muted hover:text-dark"
        >
          <X size={18} />
        </button>
      )}
    </div>
  )
}