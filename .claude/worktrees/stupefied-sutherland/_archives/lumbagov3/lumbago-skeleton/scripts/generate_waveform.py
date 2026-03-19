#!/usr/bin/env python3
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import librosa
import numpy as np

def generate_waveform(path, outpath):
    y, sr = librosa.load(path, sr=None)
    hop = max(1, int(len(y)/1000))
    y_small = y[::hop]
    times = np.linspace(0, len(y)/sr, num=len(y_small))
    plt.figure(figsize=(10,2))
    plt.fill_between(times, y_small, color='k')
    plt.axis('off')
    plt.savefig(outpath, bbox_inches='tight', pad_inches=0)
    plt.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: generate_waveform.py <audio> <outpng>')
        sys.exit(1)
    generate_waveform(sys.argv[1], sys.argv[2])
