'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const nav = [
  { href: '/', label: 'Dashboard', icon: '📊' },
  { href: '/campaigns', label: 'Campaigns', icon: '🎯' },
  { href: '/content', label: 'Content', icon: '📝' },
  { href: '/reddit', label: 'Reddit', icon: '💬' },
  { href: '/ads', label: 'Ads', icon: '📢' },
  { href: '/analytics', label: 'Analytics', icon: '📈' },
  { href: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-bg-card border-r border-border-subtle flex flex-col">
      <div className="p-5 border-b border-border-subtle">
        <h1 className="text-xl font-bold text-white">Marketing Engine</h1>
        <p className="text-xs text-text-muted mt-1">AI-Powered Automation</p>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {nav.map((item) => {
          const isActive = item.href === '/'
            ? pathname === '/'
            : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-accent-blue/10 text-accent-blue font-medium'
                  : 'text-text-muted hover:text-white hover:bg-bg-hover'
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-border-subtle">
        <div className="text-xs text-text-muted">
          <p>ELAV8 Builds</p>
          <p className="mt-1 opacity-60">v1.0.0</p>
        </div>
      </div>
    </aside>
  );
}
