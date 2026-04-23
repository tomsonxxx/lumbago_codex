import React from 'react';
import { AudioFile, ProcessingState } from '../types';

interface DashboardTabProps {
  files: AudioFile[];
  isRunning: boolean;
  onSmartScan: () => void;
  onOpenLibrary: () => void;
}

const DashboardTab: React.FC<DashboardTabProps> = ({ files, isRunning, onSmartScan, onOpenLibrary }) => {
  const processing = files.filter((file) => file.state === ProcessingState.PROCESSING).length;
  const success = files.filter((file) => file.state === ProcessingState.SUCCESS).length;
  const errors = files.filter((file) => file.state === ProcessingState.ERROR).length;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Dashboard v1</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Uruchom 6-krokowy pipeline: local parsing, source probing, AI consensus i zapis tagów.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={onSmartScan}
              disabled={isRunning || files.length === 0}
              className="rounded-lg bg-gradient-to-r from-cyan-400 to-emerald-400 px-4 py-2 text-sm font-bold text-slate-900 shadow-md transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {isRunning ? 'SMART AI Skan trwa...' : 'SMART AI Skan'}
            </button>
            <button
              onClick={onOpenLibrary}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              Otwórz bibliotekę
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric title="Pliki w bibliotece" value={files.length} tone="slate" />
        <Metric title="Processing" value={processing} tone="cyan" />
        <Metric title="Sukces" value={success} tone="green" />
        <Metric title="Błędy" value={errors} tone="magenta" />
      </div>
    </div>
  );
};

const Metric: React.FC<{ title: string; value: number; tone: 'slate' | 'cyan' | 'green' | 'magenta' }> = ({ title, value, tone }) => {
  const tones = {
    slate: 'border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200',
    cyan: 'border-cyan-300 bg-cyan-50 text-cyan-800 dark:border-cyan-800 dark:bg-cyan-900/20 dark:text-cyan-300',
    green: 'border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-300',
    magenta: 'border-fuchsia-300 bg-fuchsia-50 text-fuchsia-800 dark:border-fuchsia-800 dark:bg-fuchsia-900/20 dark:text-fuchsia-300',
  };

  return (
    <div className={`rounded-xl border p-4 shadow-sm ${tones[tone]}`}>
      <p className="text-xs font-semibold uppercase tracking-wider">{title}</p>
      <p className="mt-2 text-2xl font-bold">{value}</p>
    </div>
  );
};

export default DashboardTab;

