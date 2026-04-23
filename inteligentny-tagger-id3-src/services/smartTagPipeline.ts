import { analyzeWithProviders, ApiKeys } from './aiService';
import { applyTags, isTagWritingSupported, readID3Tags, saveFileDirectly } from '../utils/audioUtils';
import {
  AudioFile,
  DataOrigin,
  ID3Tags,
  PipelineError,
  ProcessingState,
  SmartTagRun,
  SourceProbeResult,
  TagFieldConfidence,
  TaggingDecision,
} from '../types';

type ScanTarget = 'selected' | 'all';

interface SmartTagPipelineOptions {
  files: AudioFile[];
  directoryHandle: any | null;
  apiKeys: ApiKeys;
  confidenceThreshold?: number;
  onFileUpdate: (fileId: string, patch: Partial<AudioFile>) => void;
}

interface SmartScanResult {
  processed: number;
  success: number;
  errors: number;
}

const MANDATORY_SOURCES: Array<{
  key: SourceProbeResult['source'];
  siteQuery: string;
  hint: string;
}> = [
  { key: 'google', siteQuery: '', hint: '' },
  { key: 'beatport', siteQuery: 'site:beatport.com/track', hint: 'beatport.com/track' },
  { key: 'traxsource', siteQuery: 'site:traxsource.com/track', hint: 'traxsource.com/track' },
  { key: 'discogs', siteQuery: 'site:discogs.com/release', hint: 'discogs.com/release' },
  { key: 'juno', siteQuery: 'site:junodownload.com', hint: 'junodownload.com' },
];

const CONSENSUS_FIELDS: (keyof ID3Tags)[] = [
  'title',
  'artist',
  'album',
  'year',
  'genre',
  'bpm',
  'key',
  'trackNumber',
  'discNumber',
  'albumArtist',
  'composer',
  'mood',
];

const generateRunId = () => `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

const hasValue = (value: unknown) => !(value === null || value === undefined || value === '');

export const parseFilename = (fileName: string): Partial<ID3Tags> => {
  const stem = fileName.replace(/\.[a-z0-9]+$/i, '').replace(/_/g, ' ').trim();
  const match = stem.match(/^(?:\d{1,3}\s*[-._]\s*)?(?<artist>.+?)\s*-\s*(?<title>.+?)(?:\s*\((?<extra>.*?)\))?$/);
  if (!match?.groups) {
    return {};
  }
  const artist = match.groups.artist?.trim();
  const title = match.groups.title?.trim();
  const remix = match.groups.extra?.trim();
  const out: Partial<ID3Tags> = {};
  if (artist) {
    out.artist = artist;
  }
  if (title) {
    out.title = title;
  }
  if (remix && !out.comments) {
    out.comments = `Version: ${remix}`;
  }
  return out;
};

const buildLookupQuery = (tags: Partial<ID3Tags>, fallbackName: string) => {
  const artist = tags.artist?.trim();
  const title = tags.title?.trim();
  if (artist && title) {
    return `${artist} ${title}`;
  }
  return fallbackName.replace(/\.[a-z0-9]+$/i, '');
};

const probeOneSource = async (query: string, source: typeof MANDATORY_SOURCES[number]): Promise<SourceProbeResult> => {
  const fullQuery = source.siteQuery ? `${source.siteQuery} ${query}` : query;
  const encoded = encodeURIComponent(fullQuery);
  const url = `https://r.jina.ai/http://duckduckgo.com/?q=${encoded}`;
  try {
    const response = await fetch(url, { headers: { 'User-Agent': 'LumbagoSmartTag/1.0' } });
    if (!response.ok) {
      return { source: source.key, status: 'error', query: fullQuery, detail: `HTTP ${response.status}` };
    }
    const body = (await response.text()).toLowerCase();
    if (!source.hint) {
      return { source: source.key, status: body.length > 0 ? 'hit' : 'miss', query: fullQuery, url };
    }
    const hit = body.includes(source.hint);
    return {
      source: source.key,
      status: hit ? 'hit' : 'miss',
      query: fullQuery,
      detail: hit ? 'domain match' : 'no match',
      url,
    };
  } catch (error) {
    return {
      source: source.key,
      status: 'error',
      query: fullQuery,
      detail: error instanceof Error ? error.message : 'Source probe failed',
      url,
    };
  }
};

const probeSources = async (query: string): Promise<SourceProbeResult[]> => {
  const probes = await Promise.all(MANDATORY_SOURCES.map((source) => probeOneSource(query, source)));
  return probes;
};

const fetchCoverHint = async (query: string): Promise<string | undefined> => {
  try {
    const response = await fetch(`https://itunes.apple.com/search?term=${encodeURIComponent(query)}&entity=song&limit=1`);
    if (!response.ok) {
      return undefined;
    }
    const data = await response.json();
    const artwork = data?.results?.[0]?.artworkUrl100;
    if (!artwork) {
      return undefined;
    }
    return String(artwork).replace('100x100bb', '600x600bb');
  } catch {
    return undefined;
  }
};

const buildPrompt = (query: string, localTags: Partial<ID3Tags>, sourceProbes: SourceProbeResult[]) => {
  const sourcesSummary = sourceProbes
    .map((probe) => `${probe.source}:${probe.status}${probe.detail ? `(${probe.detail})` : ''}`)
    .join(', ');
  return `Track query: ${query}
Local tags: ${JSON.stringify(localTags)}
Mandatory source probe status: ${sourcesSummary}
Generate best ID3 tags and confidence.`;
};

const normalizeComparable = (value: unknown) => {
  if (value === null || value === undefined) {
    return '';
  }
  return String(value).trim().toLowerCase();
};

export const scoreConsensus = (
  providers: Awaited<ReturnType<typeof analyzeWithProviders>>,
  existing: Partial<ID3Tags>,
  threshold: number
): { accepted: Partial<ID3Tags>; rejected: (keyof ID3Tags)[]; confidences: TagFieldConfidence[] } => {
  const accepted: Partial<ID3Tags> = {};
  const rejected: (keyof ID3Tags)[] = [];
  const confidences: TagFieldConfidence[] = [];

  for (const field of CONSENSUS_FIELDS) {
    const voteBucket = new Map<string, { value: unknown; score: number; byProvider: Record<string, number> }>();

    for (const providerResult of providers) {
      const value = providerResult.tags[field];
      if (!hasValue(value)) {
        continue;
      }
      const key = normalizeComparable(value);
      const current = voteBucket.get(key) ?? { value, score: 0, byProvider: {} };
      const baseScore = Math.max(0.05, providerResult.confidence || 0.5);
      current.score += baseScore;
      current.byProvider[providerResult.provider] = baseScore;
      voteBucket.set(key, current);
    }

    let winner: { value: unknown; score: number; byProvider: Record<string, number> } | undefined;
    for (const candidate of voteBucket.values()) {
      if (!winner || candidate.score > winner.score) {
        winner = candidate;
      }
    }

    const confidence = Math.max(
      0,
      Math.min(
        1,
        winner
          ? winner.score / Math.max(1, providers.filter((providerResult) => !providerResult.error).length)
          : 0
      )
    );

    confidences.push({
      field,
      confidence,
      byProvider: winner?.byProvider ?? {},
    });

    if (winner && confidence >= threshold) {
      accepted[field] = winner.value as never;
    } else if (hasValue(existing[field])) {
      accepted[field] = existing[field] as never;
      rejected.push(field);
    } else {
      rejected.push(field);
    }
  }

  return { accepted, rejected, confidences };
};

export const appendDataOriginComment = (tags: Partial<ID3Tags>, provenance: DataOrigin) => {
  const line = `Data Origin: ${JSON.stringify(provenance)}`;
  const comments = tags.comments?.trim();
  if (!comments) {
    tags.comments = line;
    return;
  }
  if (comments.includes('Data Origin:')) {
    tags.comments = comments.replace(/Data Origin:\s*\{.*\}$/s, line);
    return;
  }
  tags.comments = `${comments}\n${line}`;
};

export class SmartTagPipeline {
  private readonly files: AudioFile[];
  private readonly directoryHandle: any | null;
  private readonly apiKeys: ApiKeys;
  private readonly confidenceThreshold: number;
  private readonly onFileUpdate: SmartTagPipelineOptions['onFileUpdate'];

  constructor(options: SmartTagPipelineOptions) {
    this.files = options.files;
    this.directoryHandle = options.directoryHandle;
    this.apiKeys = options.apiKeys;
    this.confidenceThreshold = options.confidenceThreshold ?? 0.62;
    this.onFileUpdate = options.onFileUpdate;
  }

  async runSmartScan(target: ScanTarget, fileIds?: string[]): Promise<SmartScanResult> {
    const selected = this.files.filter((file) => (target === 'all' ? true : fileIds?.includes(file.id)));
    let success = 0;
    let errors = 0;
    let processed = 0;

    for (const file of selected) {
      const run = await this.processFile(file, (file.retryCount ?? 0) + 1);
      processed += 1;
      if (run.status === 'SUCCESS') {
        success += 1;
      } else {
        errors += 1;
      }
    }

    return { processed, success, errors };
  }

  async retryTagging(fileId: string): Promise<SmartTagRun | undefined> {
    const file = this.files.find((candidate) => candidate.id === fileId);
    if (!file) {
      return undefined;
    }
    return this.processFile(file, (file.retryCount ?? 0) + 1);
  }

  private async processFile(file: AudioFile, attempt: number): Promise<SmartTagRun> {
    const runId = generateRunId();
    const startedAt = new Date().toISOString();
    const processingRun: SmartTagRun = { runId, startedAt, status: 'PROCESSING', attempts: attempt };

    this.onFileUpdate(file.id, {
      state: ProcessingState.PROCESSING,
      smartTagRun: processingRun,
      retryCount: attempt,
      errorMessage: undefined,
    });

    try {
      // Step 2: local parsing
      const fileTags = await readID3Tags(file.file).catch(() => ({}));
      const nameTags = parseFilename(file.file.name);
      const localTags: Partial<ID3Tags> = { ...file.originalTags, ...fileTags, ...nameTags };
      const query = buildLookupQuery(localTags, file.file.name);

      // Step 3: mandatory source probing
      const sourceProbes = await probeSources(query);

      // Step 4: AI parallel consensus
      const prompt = buildPrompt(query, localTags, sourceProbes);
      const providerOutputs = await analyzeWithProviders(prompt, this.apiKeys);
      const consensus = scoreConsensus(providerOutputs, localTags, this.confidenceThreshold);
      const coverUrl = localTags.albumCoverUrl || (await fetchCoverHint(query));
      if (coverUrl) {
        consensus.accepted.albumCoverUrl = coverUrl;
      }

      const provenance: DataOrigin = {
        timestamp: new Date().toISOString(),
        providers: providerOutputs.map((item) => item.provider),
        modelVersions: Object.fromEntries(providerOutputs.map((item) => [item.provider, item.model])),
        sources: sourceProbes,
        fieldConfidence: consensus.confidences,
      };

      appendDataOriginComment(consensus.accepted, provenance);

      const decision: TaggingDecision = {
        proposedTags: consensus.accepted as ID3Tags,
        acceptedFields: Object.keys(consensus.accepted) as (keyof ID3Tags)[],
        rejectedFields: consensus.rejected,
        provenance,
      };

      // Step 5: physical write
      const updatedFile = await this.writePhysical(file, decision.proposedTags);

      // Step 6: confirmation/logging
      const finishedRun: SmartTagRun = {
        ...processingRun,
        status: 'SUCCESS',
        finishedAt: new Date().toISOString(),
        decision,
      };

      this.onFileUpdate(file.id, {
        ...updatedFile,
        fetchedTags: {
          ...(file.fetchedTags || file.originalTags || {}),
          ...decision.proposedTags,
        },
        state: ProcessingState.SUCCESS,
        smartTagRun: finishedRun,
      });
      return finishedRun;
    } catch (error) {
      const pipelineError: PipelineError = {
        code: 'PIPELINE_UNEXPECTED',
        message: error instanceof Error ? error.message : 'Unknown pipeline error',
        step: 6,
        retriable: true,
      };
      const failedRun: SmartTagRun = {
        ...processingRun,
        status: 'ERROR',
        finishedAt: new Date().toISOString(),
        error: pipelineError,
      };
      this.onFileUpdate(file.id, {
        state: ProcessingState.ERROR,
        smartTagRun: failedRun,
        errorMessage: pipelineError.message,
      });
      return failedRun;
    }
  }

  private async writePhysical(file: AudioFile, proposedTags: ID3Tags): Promise<Partial<AudioFile>> {
    if (!isTagWritingSupported(file.file)) {
      return {};
    }
    if (this.directoryHandle && file.handle) {
      const saveResult = await saveFileDirectly(this.directoryHandle, { ...file, fetchedTags: proposedTags });
      if (!saveResult.success || !saveResult.updatedFile) {
        throw new Error(saveResult.errorMessage || 'Write to disk failed');
      }
      return {
        file: saveResult.updatedFile.file,
        handle: saveResult.updatedFile.handle,
      };
    }

    const taggedBlob = await applyTags(file.file, proposedTags);
    const rewritten = new File([taggedBlob], file.file.name, {
      type: file.file.type,
      lastModified: Date.now(),
    });
    return { file: rewritten };
  }
}
