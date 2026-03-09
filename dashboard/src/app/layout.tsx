import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/Sidebar';

export const metadata: Metadata = {
  title: 'Marketing Engine — ELAV8',
  description: 'AI-powered autonomous marketing platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-sans antialiased">
        {/* Ambient background gradient */}
        <div className="fixed inset-0 -z-10">
          <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-accent-purple/[0.03] rounded-full blur-[120px]" />
          <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-accent-teal/[0.02] rounded-full blur-[100px]" />
        </div>

        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 ml-72 p-8 overflow-auto page-enter">
            <div className="max-w-[1400px] mx-auto">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
