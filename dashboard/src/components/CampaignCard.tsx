import type { Campaign } from '@/lib/api';

interface CampaignCardProps {
  campaign: Campaign;
}

const statusColors: Record<string, string> = {
  active: 'bg-accent-green/20 text-accent-green',
  draft: 'bg-text-muted/20 text-text-muted',
  paused: 'bg-accent-yellow/20 text-accent-yellow',
  completed: 'bg-accent-blue/20 text-accent-blue',
};

export default function CampaignCard({ campaign }: CampaignCardProps) {
  return (
    <div className="bg-bg-card rounded-xl p-4 border border-border-subtle hover:border-accent-blue/30 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-white">{campaign.name}</h3>
          <p className="text-sm text-text-muted mt-0.5">{campaign.product_name}</p>
        </div>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[campaign.status] || statusColors.draft}`}>
          {campaign.status}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 text-xs">
        <div>
          <p className="text-text-muted">Channels</p>
          <p className="text-white font-mono mt-0.5">
            {campaign.channels?.length || 0}
          </p>
        </div>
        <div>
          <p className="text-text-muted">Daily Budget</p>
          <p className="text-white font-mono mt-0.5">
            ${campaign.budget_daily?.toLocaleString() || '0'}
          </p>
        </div>
        <div>
          <p className="text-text-muted">Total Budget</p>
          <p className="text-white font-mono mt-0.5">
            ${campaign.budget_total?.toLocaleString() || '0'}
          </p>
        </div>
      </div>

      {campaign.target_audience && (
        <p className="text-xs text-text-muted mt-3 truncate">
          Target: {campaign.target_audience}
        </p>
      )}
    </div>
  );
}
