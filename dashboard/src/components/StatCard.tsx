interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon?: string;
  gradient?: 'purple' | 'teal' | 'orange' | 'pink' | 'default';
}

const gradientMap = {
  purple: 'gradient-card-purple',
  teal: 'gradient-card-teal',
  orange: 'gradient-card-orange',
  pink: 'gradient-card-pink',
  default: 'gradient-card',
};

const iconBgMap = {
  purple: 'from-accent-purple/20 to-accent-purple/5',
  teal: 'from-accent-teal/20 to-accent-teal/5',
  orange: 'from-accent-orange/20 to-accent-orange/5',
  pink: 'from-accent-pink/20 to-accent-pink/5',
  default: 'from-accent-blue/20 to-accent-blue/5',
};

export default function StatCard({ label, value, subtext, trend, icon, gradient = 'default' }: StatCardProps) {
  const trendIcon = trend === 'up' ? '↑' : trend === 'down' ? '↓' : '';
  const trendColor =
    trend === 'up' ? 'text-accent-green' :
    trend === 'down' ? 'text-accent-red' :
    'text-zinc-500';

  return (
    <div className={`${gradientMap[gradient]} glass rounded-2xl p-5 group hover:border-white/10 transition-all duration-300 ambient-glow`}>
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs text-zinc-500 font-medium uppercase tracking-wider">{label}</p>
        {icon && (
          <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${iconBgMap[gradient]} flex items-center justify-center`}>
            <span className="text-sm">{icon}</span>
          </div>
        )}
      </div>
      <p className="text-3xl font-bold text-white font-mono count-up tracking-tight">{value}</p>
      {subtext && (
        <p className={`text-xs mt-2 flex items-center gap-1 ${trendColor}`}>
          {trendIcon && <span className="font-bold">{trendIcon}</span>}
          {subtext}
        </p>
      )}
    </div>
  );
}
