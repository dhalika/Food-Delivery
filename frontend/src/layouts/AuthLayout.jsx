import Logo from '../components/common/Logo'
import { UtensilsCrossed, Truck, Store, Shield } from 'lucide-react'

export default function AuthLayout({ children }) {
  return (
    <div className="min-h-screen flex">
      {/* LEFT SIDE - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-brand-400 via-brand-500 to-brand-600 p-12 flex-col justify-between relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 text-9xl">🍕</div>
          <div className="absolute top-40 right-20 text-9xl">🍔</div>
          <div className="absolute bottom-20 left-20 text-9xl">🍜</div>
          <div className="absolute bottom-40 right-40 text-9xl">🥡</div>
        </div>

        <div className="relative z-10">
          <Logo size="large" />
        </div>

        <div className="relative z-10 space-y-6">
          <h2 className="text-5xl font-display font-extrabold text-dark leading-tight">
            Delicious food,<br />
            delivered fast 🥡
          </h2>
          <p className="text-dark text-lg opacity-80">
            Order from your favorite restaurants in just a few taps.
          </p>

          <div className="grid grid-cols-2 gap-4 pt-6">
            <Feature icon={<UtensilsCrossed />} label="1000+ Restaurants" />
            <Feature icon={<Truck />} label="Fast Delivery" />
            <Feature icon={<Store />} label="Top Brands" />
            <Feature icon={<Shield />} label="Safe Payments" />
          </div>
        </div>

        <p className="relative z-10 text-dark text-sm opacity-60">
          © 2026 HongKong • All rights reserved
        </p>
      </div>

      {/* RIGHT SIDE - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 bg-cream">
        <div className="w-full max-w-md animate-slide-up">
          <div className="lg:hidden mb-8 text-center">
            <Logo size="medium" />
          </div>
          {children}
        </div>
      </div>
    </div>
  )
}

function Feature({ icon, label }) {
  return (
    <div className="flex items-center gap-2 text-dark">
      <div className="bg-white/30 p-2 rounded-lg">{icon}</div>
      <span className="font-semibold text-sm">{label}</span>
    </div>
  )
}