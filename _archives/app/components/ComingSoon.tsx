
import React from 'react';

export const ComingSoon = ({ title, desc }: { title: string, desc?: string }) => (
  <div className="flex flex-col items-center justify-center h-64 text-gray-500 border border-dashed border-gray-700 rounded-lg bg-gray-800/30">
    <div className="text-4xl mb-4 opacity-50">🚧</div>
    <h3 className="text-xl font-semibold text-gray-300">{title}</h3>
    <p className="mt-2 text-sm">{desc || "Ta funkcja jest w trakcie implementacji (Faza 4-6)."}</p>
  </div>
);
