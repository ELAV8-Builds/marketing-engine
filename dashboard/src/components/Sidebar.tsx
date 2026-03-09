'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const nav = [
  { href: '/', label: 'Dashboard', icon: '⚡' },
  { href: '/campaigns', label: 'Campaigns', icon: '🎯' },
  { href: '/content', label: 'Content', icon: '✨' },
  { href: '/video', label: 'Video', icon: '🎬' },
  { href: '/logos', label: 'Logos', icon: '🎨' },
  { href: '/reddit', label: 'Reddit', icon: '💬' },
  { href: '/ads', label: 'Ads', icon: '📡' },
  { href: '/analytics', label: 'Analytics', icon: '📊' },
  { href: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-72 glass flex flex-col z-50">
      {/* Logo */}
      <div className="p-6 border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent-purple to-accent-teal flex items-center justify-center">
            <span className="text-white font-bold text-sm">ME</span>
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight">Marketing Engine</h1>
            <p className="text-[10px] text-zinc-500 uppercase tracking-widest font-medium">by ELAV8</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-0.5">
        <p className="px-3 py-2 text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Navigation</p>
        {nav.map((item) => {
          const isActive = item.href === '/'
            ? pathname === '/'
            : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-200 ${
                isActive
                  ? 'bg-accent-purple/10 text-white font-medium shadow-[inset_0_0_0_1px_rgba(124,92,252,0.2)]'
                  : 'text-zinc-400 hover:text-white hover:bg-white/[0.03]'
              }`}
            >
              <span className={`text-base transition-transform duration-200 ${isActive ? 'scale-110' : 'group-hover:scale-110'}`}>
                {item.icon}
              </span>
              {item.label}
              {isActive && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-accent-purple live-pulse" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-white/[0.06]">
        <div className="glass rounded-xl p-3">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-accent-green live-pulse" />
            <span className="text-xs text-zinc-400">Engine Status</span>
          </div>
          <p className="text-xs text-zinc-500">
            v1.2.0 · <span className="text-accent-teal">Online</span>
          </p>
        </div>
      </div>
    </aside>
  );
}
