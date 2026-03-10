'use client';

import { useState } from 'react';
import LogoGenerator, { LogoResult } from './LogoGenerator';
import LogoGallery from './LogoGallery';

export default function LogosPage() {
  const [results, setResults] = useState<LogoResult[]>([]);
  const [loading, setLoading] = useState(false);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Logo Generator</h1>
        <p className="text-sm text-zinc-500 mt-1">AI-powered brand identity creation with Recraft, Ideogram, or DALL-E</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        <LogoGenerator onResults={setResults} />

        <div className="lg:col-span-3">
          <LogoGallery results={results} loading={loading} count={4} />
        </div>
      </div>
    </div>
  );
}
