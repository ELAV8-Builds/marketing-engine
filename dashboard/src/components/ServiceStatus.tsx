interface ServiceStatusProps {
  services: Record<string, boolean>;
  connected: boolean;
}

export default function ServiceStatus({ services, connected }: ServiceStatusProps) {
  return (
    <div className="bg-bg-card rounded-xl p-4 border border-border-subtle">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider">Services</h3>
        {connected ? (
          <span className="px-2 py-0.5 bg-accent-green/20 text-accent-green text-xs rounded-full">
            Connected
          </span>
        ) : (
          <span className="px-2 py-0.5 bg-accent-red/20 text-accent-red text-xs rounded-full">
            Offline
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2">
        {Object.entries(services).map(([name, active]) => (
          <div
            key={name}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-bg-main"
          >
            <div
              className={`w-2 h-2 rounded-full ${
                active ? 'bg-accent-green' : 'bg-text-muted'
              }`}
            />
            <span className="text-xs text-white capitalize">{name.replace('_', ' ')}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
