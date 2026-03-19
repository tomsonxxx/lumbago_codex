"""Duplicate Finder module

This module provides three comparison methods:
- hash_compare: exact file hash compare
- tag_similarity: fuzzy compare on title/artist/duration
- fingerprint_similarity: acoustic fingerprint similarity (mocked)

The main function `find_duplicates(tracks, thresholds)` accepts a list of track dicts
and returns groups of duplicates with scores and methods used.
"""
import hashlib
import difflib
from typing import List, Dict, Any

def hash_compare(track_a: Dict[str, Any], track_b: Dict[str, Any]) -> bool:
    ha = track_a.get('file_hash')
    hb = track_b.get('file_hash')
    if not ha or not hb:
        return False
    return ha == hb

def tag_similarity(track_a: Dict[str, Any], track_b: Dict[str, Any]) -> float:
    # Use simple SequenceMatcher on title+artist
    a = (track_a.get('title','') + ' ' + track_a.get('artist','')).lower()
    b = (track_b.get('title','') + ' ' + track_b.get('artist','')).lower()
    if not a.strip() or not b.strip():
        return 0.0
    score = difflib.SequenceMatcher(None, a, b).ratio()
    # duration proximity bonus
    dur_a = track_a.get('duration') or 0
    dur_b = track_b.get('duration') or 0
    if dur_a and dur_b:
        diff = abs(dur_a - dur_b)
        if diff < 3:
            score = min(1.0, score + 0.15)
        elif diff < 8:
            score = min(1.0, score + 0.05)
    return score

def fingerprint_similarity(track_a: Dict[str, Any], track_b: Dict[str, Any]) -> float:
    # Mocked: if fingerprint exists, compare string similarity
    fa = track_a.get('fingerprint')
    fb = track_b.get('fingerprint')
    if not fa or not fb:
        return 0.0
    # simple hamming-like via difflib for placeholder
    return difflib.SequenceMatcher(None, fa, fb).ratio()

def find_duplicates(tracks: List[Dict[str, Any]], thresholds=None):
    if thresholds is None:
        thresholds = {'hash': True, 'tag': 0.85, 'fingerprint': 0.75}
    groups = []
    seen = set()
    n = len(tracks)
    for i in range(n):
        if i in seen:
            continue
        a = tracks[i]
        group = {'tracks': [a], 'matches': []}
        for j in range(i+1, n):
            if j in seen:
                continue
            b = tracks[j]
            method = None
            score = 0.0
            if thresholds.get('hash') and hash_compare(a,b):
                method = 'hash'
                score = 1.0
            else:
                fscore = fingerprint_similarity(a,b)
                tscore = tag_similarity(a,b)
                if fscore >= thresholds.get('fingerprint',0.75):
                    method = 'fingerprint'
                    score = fscore
                elif tscore >= thresholds.get('tag',0.85):
                    method = 'tag'
                    score = tscore
            if method:
                group['tracks'].append(b)
                group['matches'].append({'index': j, 'method': method, 'score': score})
                seen.add(j)
        if len(group['tracks'])>1:
            groups.append(group)
    return groups
