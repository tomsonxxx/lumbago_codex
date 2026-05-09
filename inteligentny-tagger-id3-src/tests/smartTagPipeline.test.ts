import { describe, expect, it } from 'vitest';
import { appendDataOriginComment, parseFilename, scoreConsensus } from '../services/smartTagPipeline';
import { DataOrigin, ID3Tags } from '../types';

describe('smartTagPipeline', () => {
  it('parses artist and title from filename', () => {
    const parsed = parseFilename('01 - Tale Of Us - Silent Space (Afterhours Mix).mp3');
    expect(parsed.artist).toBe('Tale Of Us');
    expect(parsed.title).toBe('Silent Space');
    expect(parsed.comments).toContain('Afterhours Mix');
  });

  it('selects consensus values by weighted confidence', () => {
    const providers = [
      { provider: 'gemini', model: 'gemini-2.5-flash', tags: { title: 'Track A', artist: 'Artist A', bpm: 125 }, confidence: 0.9 },
      { provider: 'openai', model: 'gpt-4.1-mini', tags: { title: 'Track A', artist: 'Artist A', bpm: 125 }, confidence: 0.8 },
      { provider: 'grok', model: 'grok-2-latest', tags: { title: 'Track B', artist: 'Artist A', bpm: 124 }, confidence: 0.3 },
    ];
    const result = scoreConsensus(providers as any, {}, 0.55);
    expect(result.accepted.title).toBe('Track A');
    expect(result.accepted.artist).toBe('Artist A');
    expect(result.accepted.bpm).toBe(125);
    expect(result.confidences.find((item) => item.field === 'title')?.confidence).toBeGreaterThan(0.55);
  });

  it('serializes Data Origin into comments field', () => {
    const tags: Partial<ID3Tags> = { comments: 'Original note' };
    const provenance: DataOrigin = {
      timestamp: '2026-04-23T12:00:00.000Z',
      providers: ['gemini'],
      modelVersions: { gemini: 'gemini-2.5-flash' },
      sources: [
        { source: 'google', status: 'hit', query: 'artist title', detail: 'ok' },
        { source: 'beatport', status: 'miss', query: 'beatport artist title' },
        { source: 'traxsource', status: 'miss', query: 'traxsource artist title' },
        { source: 'discogs', status: 'hit', query: 'discogs artist title' },
        { source: 'juno', status: 'miss', query: 'juno artist title' },
      ],
      fieldConfidence: [],
    };
    appendDataOriginComment(tags, provenance);
    expect(tags.comments).toContain('Original note');
    expect(tags.comments).toContain('Data Origin:');
    expect(tags.comments).toContain('"providers":["gemini"]');
  });
});

