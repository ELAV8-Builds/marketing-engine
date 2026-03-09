import type { ContentItem } from '@/lib/api';

interface ContentTableProps {
  items: ContentItem[];
}

const typeIcons: Record<string, string> = {
  video_short: '🎬',
  reddit_comment: '💬',
  ad_creative: '📢',
  landing_page: '🌐',
  blog_post: '📝',
};

const statusColors: Record<string, string> = {
  ready: 'text-accent-blue',
  published: 'text-accent-green',
  draft: 'text-text-muted',
  failed: 'text-accent-red',
};

export default function ContentTable({ items }: ContentTableProps) {
  if (items.length === 0) {
    return (
      <div className="bg-bg-card rounded-xl p-8 border border-border-subtle text-center">
        <p className="text-text-muted">No content generated yet</p>
        <p className="text-xs text-text-muted mt-1">Use the API or dashboard to generate content</p>
      </div>
    );
  }

  return (
    <div className="bg-bg-card rounded-xl border border-border-subtle overflow-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-border-subtle text-xs text-text-muted">
            <th className="py-3 px-4 text-left">Type</th>
            <th className="py-3 px-4 text-left">Title</th>
            <th className="py-3 px-4 text-left">Platform</th>
            <th className="py-3 px-4 text-left">Status</th>
            <th className="py-3 px-4 text-left">Created</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-b border-border-subtle hover:bg-bg-hover transition-colors">
              <td className="py-3 px-4 text-sm">
                <span className="mr-2">{typeIcons[item.content_type] || '📄'}</span>
                {item.content_type.replace('_', ' ')}
              </td>
              <td className="py-3 px-4 text-sm text-white max-w-xs truncate">
                {item.title}
              </td>
              <td className="py-3 px-4 text-sm text-text-muted capitalize">
                {item.platform}
              </td>
              <td className="py-3 px-4 text-sm">
                <span className={statusColors[item.status] || 'text-text-muted'}>
                  {item.status}
                </span>
              </td>
              <td className="py-3 px-4 text-xs text-text-muted">
                {new Date(item.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
