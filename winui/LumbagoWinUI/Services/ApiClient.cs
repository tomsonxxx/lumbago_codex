using System.Net.Http.Json;
using System.Text.Json;
using LumbagoWinUI.Models;

namespace LumbagoWinUI.Services;

public sealed class ApiClient
{
    private readonly HttpClient _http;
    private static readonly JsonSerializerOptions _json = new()
    {
        PropertyNameCaseInsensitive = true,
    };

    public ApiClient(string baseUrl = "http://127.0.0.1:8765")
    {
        _http = new HttpClient { BaseAddress = new Uri(baseUrl), Timeout = TimeSpan.FromSeconds(30) };
    }

    public async Task<bool> IsHealthyAsync(CancellationToken ct = default)
    {
        try
        {
            var resp = await _http.GetAsync("/health", ct);
            return resp.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public async Task<List<Track>> GetTracksAsync(CancellationToken ct = default)
    {
        // Backend returns {"tracks": [...]} wrapper, not a bare array.
        var result = await _http.GetFromJsonAsync<TracksResponse>("/tracks", _json, ct);
        return result?.Tracks ?? [];
    }

    public async Task<string?> GetSettingAsync(string key, CancellationToken ct = default)
    {
        try
        {
            var resp = await _http.GetFromJsonAsync<SettingResponse>($"/settings/{Uri.EscapeDataString(key)}", _json, ct);
            return resp?.Value;
        }
        catch (HttpRequestException)
        {
            return null;
        }
    }

    public async Task SetSettingAsync(string key, string value, CancellationToken ct = default)
    {
        var payload = new { value };
        var resp = await _http.PutAsJsonAsync($"/settings/{Uri.EscapeDataString(key)}", payload, ct);
        resp.EnsureSuccessStatusCode();
    }

    public async Task<ImportPreviewResult> ImportPreviewAsync(
        string folder, bool recursive = true, CancellationToken ct = default)
    {
        var payload = new { folder, recursive };
        var resp = await _http.PostAsJsonAsync("/tracks/import-preview", payload, ct);
        resp.EnsureSuccessStatusCode();
        return await resp.Content.ReadFromJsonAsync<ImportPreviewResult>(_json, ct)
               ?? new ImportPreviewResult();
    }

    public async Task<ImportCommitResult> ImportCommitAsync(
        IEnumerable<string> paths, CancellationToken ct = default)
    {
        var payload = new { paths = paths.ToList() };
        var resp = await _http.PostAsJsonAsync("/tracks/import-commit", payload, ct);
        resp.EnsureSuccessStatusCode();
        return await resp.Content.ReadFromJsonAsync<ImportCommitResult>(_json, ct)
               ?? new ImportCommitResult();
    }

    public async Task<DuplicatesResult> AnalyzeDuplicatesAsync(
        string mode = "metadata", CancellationToken ct = default)
    {
        var payload = new { mode };
        var resp = await _http.PostAsJsonAsync("/duplicates/analyze", payload, ct);
        resp.EnsureSuccessStatusCode();
        return await resp.Content.ReadFromJsonAsync<DuplicatesResult>(_json, ct)
               ?? new DuplicatesResult();
    }

    public async Task DeleteTrackAsync(string path, CancellationToken ct = default)
    {
        var resp = await _http.DeleteAsync(
            $"/tracks/{Uri.EscapeDataString(path)}", ct);
        resp.EnsureSuccessStatusCode();
    }

    public async Task<XmlConvertResult> ConvertXmlAsync(
        string inputPath, string outputPath, CancellationToken ct = default)
    {
        var payload = new { input_path = inputPath, output_path = outputPath };
        var resp = await _http.PostAsJsonAsync("/convert/rekordbox-to-virtualdj", payload, ct);
        resp.EnsureSuccessStatusCode();
        return await resp.Content.ReadFromJsonAsync<XmlConvertResult>(_json, ct)
               ?? new XmlConvertResult();
    }

    public async Task<Track?> UpdateTrackAsync(string path, TrackUpdate update, CancellationToken ct = default)
    {
        var resp = await _http.PutAsJsonAsync(
            $"/tracks/{Uri.EscapeDataString(path)}", update, _json, ct);
        resp.EnsureSuccessStatusCode();
        var result = await resp.Content.ReadFromJsonAsync<UpdateTrackResponse>(_json, ct);
        return result?.Track;
    }

    public async Task<List<Track>> SearchTracksAsync(string query, CancellationToken ct = default)
    {
        var all = await GetTracksAsync(ct);
        if (string.IsNullOrWhiteSpace(query)) return all;
        var q = query.ToLowerInvariant();
        return all
            .Where(t =>
                (t.Title?.ToLowerInvariant().Contains(q) ?? false) ||
                (t.Artist?.ToLowerInvariant().Contains(q) ?? false) ||
                (t.Album?.ToLowerInvariant().Contains(q) ?? false))
            .ToList();
    }

    // ── Analiza AI ───────────────────────────────────────────────────────────

    public async Task<string> CreateAnalysisJobAsync(
        IEnumerable<int>? trackIds = null, CancellationToken ct = default)
    {
        var payload = trackIds is null
            ? new { track_ids = (List<int>?)null }
            : new { track_ids = (List<int>?)trackIds.ToList() };
        var resp = await _http.PostAsJsonAsync("/analysis/jobs", payload, _json, ct);
        resp.EnsureSuccessStatusCode();
        var result = await resp.Content.ReadFromJsonAsync<AnalysisJobCreatedResponse>(_json, ct);
        return result?.JobId ?? throw new InvalidOperationException("Brak job_id w odpowiedzi.");
    }

    public async Task<AnalysisJobStatus> GetAnalysisJobAsync(string jobId, CancellationToken ct = default)
    {
        return await _http.GetFromJsonAsync<AnalysisJobStatus>($"/analysis/jobs/{jobId}", _json, ct)
               ?? throw new InvalidOperationException("Pusta odpowiedź z /analysis/jobs.");
    }

    public async Task<AnalysisApplyResponse> ApplyAnalysisJobAsync(
        string jobId,
        Dictionary<string, Dictionary<string, bool>> overrides,
        CancellationToken ct = default)
    {
        var payload = new { overrides, source_prefix = "winui_smart_tagger" };
        var resp = await _http.PostAsJsonAsync($"/analysis/jobs/{jobId}/apply", payload, _json, ct);
        resp.EnsureSuccessStatusCode();
        return await resp.Content.ReadFromJsonAsync<AnalysisApplyResponse>(_json, ct)
               ?? new AnalysisApplyResponse();
    }

    private sealed record SettingResponse(string? Value);
    private sealed record TracksResponse(List<Track>? Tracks);
    private sealed record UpdateTrackResponse(Track? Track);
}

// ── Typy wyników API ─────────────────────────────────────────────────────────

public sealed class ImportPreviewResult
{
    [System.Text.Json.Serialization.JsonPropertyName("tracks")]
    public List<Track> Tracks { get; init; } = [];

    [System.Text.Json.Serialization.JsonPropertyName("errors")]
    public List<string> Errors { get; init; } = [];
}

public sealed class ImportCommitResult
{
    [System.Text.Json.Serialization.JsonPropertyName("imported")]
    public int Imported { get; init; }

    [System.Text.Json.Serialization.JsonPropertyName("errors")]
    public List<string> Errors { get; init; } = [];
}

public sealed class DuplicateGroup
{
    [System.Text.Json.Serialization.JsonPropertyName("key")]
    public string Key { get; init; } = string.Empty;

    [System.Text.Json.Serialization.JsonPropertyName("similarity")]
    public double Similarity { get; init; }

    [System.Text.Json.Serialization.JsonPropertyName("tracks")]
    public List<Track> Tracks { get; init; } = [];
}

public sealed class DuplicatesResult
{
    [System.Text.Json.Serialization.JsonPropertyName("groups")]
    public List<DuplicateGroup> Groups { get; init; } = [];
}

public sealed class XmlConvertResult
{
    [System.Text.Json.Serialization.JsonPropertyName("converted")]
    public int Converted { get; init; }

    [System.Text.Json.Serialization.JsonPropertyName("output_path")]
    public string OutputPath { get; init; } = string.Empty;
}
