interface FeatureCardProps {
  icon: string
  title: string
  description: string
  phase: string
  gradient: string
}

export function FeatureCard({
  icon,
  title,
  description,
  phase,
  gradient,
}: FeatureCardProps) {
  return (
    <div
      className={`
        group relative overflow-hidden rounded-2xl border border-white/10 bg-white/5
        p-6 backdrop-blur-sm transition-all duration-300
        hover:border-white/20 hover:bg-white/8 hover:shadow-xl hover:-translate-y-1
      `}
    >
      {/* Gradient accent in corner */}
      <div
        className={`absolute -top-10 -right-10 h-28 w-28 rounded-full opacity-20 blur-2xl transition-opacity duration-300 group-hover:opacity-40 ${gradient}`}
      />

      <div className="relative">
        <div className="mb-4 text-3xl">{icon}</div>
        <div className="mb-1 flex items-center gap-2">
          <h3 className="font-semibold text-white">{title}</h3>
          <span className="rounded-full bg-white/10 px-2 py-0.5 text-xs text-slate-400">
            {phase}
          </span>
        </div>
        <p className="text-sm leading-relaxed text-slate-400">{description}</p>

        <div className="mt-5 flex items-center gap-2 text-xs text-slate-500 group-hover:text-slate-300 transition-colors">
          <span>Coming in later phases</span>
          <span className="group-hover:translate-x-1 transition-transform">→</span>
        </div>
      </div>
    </div>
  )
}
