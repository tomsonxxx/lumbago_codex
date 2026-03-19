
import React, { useState } from 'react';
import { Icons } from '../Icons';

export const CloudBackupSync = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [provider, setProvider] = useState<'google' | 'dropbox'>('google');
    const [lastSync, setLastSync] = useState<string>('Never');
    const [isSyncing, setIsSyncing] = useState(false);
    const [syncProgress, setSyncProgress] = useState(0);
    const [autoSync, setAutoSync] = useState(true);

    // Mock Backup History
    const [backups, setBackups] = useState([
        { id: 'bk_1', date: '2023-10-25 14:30', size: '1.2 GB', version: 'v1.0.2', status: 'Success' },
        { id: 'bk_2', date: '2023-11-02 09:15', size: '1.3 GB', version: 'v1.1.0', status: 'Success' },
    ]);

    const handleConnect = () => {
        // Simulate OAuth flow
        setTimeout(() => setIsConnected(true), 1000);
    };

    const handleDisconnect = () => {
        setIsConnected(false);
    };

    const startSync = async () => {
        setIsSyncing(true);
        setSyncProgress(0);

        // Simulate upload process
        for (let i = 0; i <= 100; i += 10) {
            setSyncProgress(i);
            await new Promise(r => setTimeout(r, 200));
        }

        const newBackup = {
            id: `bk_${Date.now()}`,
            date: new Date().toLocaleString(),
            size: '1.35 GB',
            version: `v1.1.${backups.length}`,
            status: 'Success'
        };

        setBackups([newBackup, ...backups]);
        setLastSync(new Date().toLocaleString());
        setIsSyncing(false);
    };

    return (
        <div className="space-y-6">
            {/* Connection Status Panel */}
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-medium text-gray-200 flex items-center gap-2">
                        <Icons.Cloud /> Cloud Integration
                    </h3>
                    <div className={`px-3 py-1 rounded-full text-xs font-bold ${isConnected ? 'bg-green-900 text-green-300 border border-green-700' : 'bg-gray-700 text-gray-400'}`}>
                        {isConnected ? 'CONNECTED' : 'OFFLINE'}
                    </div>
                </div>

                <div className="flex items-center gap-6">
                    <div className="flex-1 space-y-4">
                        <div className="flex gap-4">
                            <button 
                                onClick={() => setProvider('google')}
                                className={`flex-1 p-4 rounded-lg border flex flex-col items-center gap-2 transition-all ${provider === 'google' ? 'bg-blue-600/20 border-blue-500' : 'bg-gray-700 border-transparent opacity-50 hover:opacity-100'}`}
                            >
                                <span className="font-bold">Google Drive</span>
                                <span className="text-xs text-gray-400">15GB Free</span>
                            </button>
                            <button 
                                onClick={() => setProvider('dropbox')}
                                className={`flex-1 p-4 rounded-lg border flex flex-col items-center gap-2 transition-all ${provider === 'dropbox' ? 'bg-blue-600/20 border-blue-500' : 'bg-gray-700 border-transparent opacity-50 hover:opacity-100'}`}
                            >
                                <span className="font-bold">Dropbox</span>
                                <span className="text-xs text-gray-400">2GB Free</span>
                            </button>
                        </div>
                    </div>
                    
                    <div className="w-px h-24 bg-gray-700"></div>

                    <div className="flex flex-col gap-3 min-w-[200px]">
                        {!isConnected ? (
                            <button onClick={handleConnect} className="w-full py-2 bg-blue-600 hover:bg-blue-500 rounded font-bold">
                                Connect Account
                            </button>
                        ) : (
                            <>
                                <button onClick={startSync} disabled={isSyncing} className="w-full py-2 bg-green-600 hover:bg-green-500 rounded font-bold disabled:opacity-50">
                                    {isSyncing ? `Syncing ${syncProgress}%...` : 'Sync Now'}
                                </button>
                                <button onClick={handleDisconnect} className="w-full py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm">
                                    Disconnect
                                </button>
                            </>
                        )}
                        <div className="text-xs text-gray-500 text-center">
                            Last Sync: {lastSync}
                        </div>
                    </div>
                </div>
            </div>

            {/* Settings & History */}
            {isConnected && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="md:col-span-2 bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-700 bg-gray-900/50 flex justify-between items-center">
                            <h4 className="font-medium text-gray-300">Backup History</h4>
                            <span className="text-xs text-gray-500">{backups.length} Versions</span>
                        </div>
                        <div className="divide-y divide-gray-700">
                            {backups.map(bk => (
                                <div key={bk.id} className="px-6 py-4 flex justify-between items-center hover:bg-gray-700/30">
                                    <div>
                                        <div className="font-medium text-gray-200">{bk.date}</div>
                                        <div className="text-xs text-gray-500 flex gap-2">
                                            <span>{bk.version}</span> • <span>{bk.size}</span>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <span className="text-xs text-green-400 bg-green-900/30 px-2 py-1 rounded">{bk.status}</span>
                                        <button className="text-xs text-blue-400 hover:underline">Restore</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 h-fit">
                        <h4 className="font-medium text-gray-300 mb-4">Sync Settings</h4>
                        <div className="space-y-4">
                            <label className="flex items-center justify-between cursor-pointer">
                                <span className="text-sm text-gray-400">Auto-Sync on Exit</span>
                                <input type="checkbox" checked={autoSync} onChange={e => setAutoSync(e.target.checked)} className="rounded text-blue-500" />
                            </label>
                            <label className="flex items-center justify-between cursor-pointer">
                                <span className="text-sm text-gray-400">Sync Metadata Only</span>
                                <input type="checkbox" className="rounded text-blue-500" defaultChecked />
                            </label>
                            <label className="flex items-center justify-between cursor-pointer">
                                <span className="text-sm text-gray-400">Backup Analysis Data</span>
                                <input type="checkbox" className="rounded text-blue-500" defaultChecked />
                            </label>
                            
                            <hr className="border-gray-700 my-2" />
                            
                            <div className="text-xs text-gray-500">
                                Storage Used: <span className="text-gray-300">4.5 GB / 15 GB</span>
                            </div>
                            <div className="w-full bg-gray-700 h-2 rounded-full overflow-hidden">
                                <div className="bg-blue-500 h-full w-[30%]"></div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
