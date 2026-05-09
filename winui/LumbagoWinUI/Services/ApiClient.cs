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
        var result = await _http.GetFromJsonAsync<List<Track>>("/tracks", _json, ct);
        return result ?? [];
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
        await _http.PutAsJsonAsync($"/settings/{Uri.EscapeDataString(key)}", payload, ct);
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

    private sealed record SettingResponse(string? Value);
}
