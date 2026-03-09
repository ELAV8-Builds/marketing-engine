interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon?: string;
}

export default function StatCard({ label, value, subtext, trend, icon }: StatCardProps) {
  const trendColor =
    trend === 'up' ? 'text-accent-green' :
    trend === 'down' ? 'text-accent-red' :
    'text-text-muted';

  return (
    <div className="bg-bg-card rounded-xl p-4 border border-border-subtle">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-text-muted uppercase tracking-wider">{label}</p>
        {icon && <span className="text-lg">{icon}</span>}
      </div>
      <p className="text-2xl font-bold text-white font-mono">{value}</p>
      {subtext && (
        <p className={`text-xs mt-1 ${trendColor}`}>{subtext}</p>
      )}
    </div>
  );
}
