

import React from 'react';
import FileDropzone from './FileDropzone';
import DirectoryConnect from './DirectoryConnect';

interface ScanTabProps {
    onFilesSelected: (files: FileList) => void;
    onUrlSubmitted: (url: string) => Promise<void>;
    onDirectoryConnect: (handle: any) => void;
    isProcessing: boolean;
}

const ScanTab: React.FC<ScanTabProps> = (props) => {
    const isFileSystemAccessSupported = 'showDirectoryPicker' in window || (window as any).aistudio?.showDirectoryPicker;

    return (
        <div className="animate-fade-in">
            <FileDropzone {...props} />

            {isFileSystemAccessSupported && (
                <>
                    <div className="relative flex items-center w-full max-w-lg mx-auto my-6">
                        <div className="flex-grow border-t border-slate-300 dark:border-slate-700"></div>
                        <span className="flex-shrink mx-4 text-slate-400 dark:text-slate-500 text-sm font-bold">LUB</span>
                        <div className="flex-grow border-t border-slate-300 dark:border-slate-700"></div>
                    </div>
                    <DirectoryConnect onDirectoryConnect={props.onDirectoryConnect} />
                </>
            )}
        </div>
    );
};

export default ScanTab;