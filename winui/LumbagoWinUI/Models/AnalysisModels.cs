using System.Text.Json;
using System.Text.Json.Serialization;

namespace LumbagoWinUI.Models;

public sealed class AnalysisDecisionApi
{
    [JsonPropertyName("field")]
    public string Field { get; init; } = string.Empty;

    /// <summary>
    /// Może być stringiem lub liczbą (np. BPM, energy).
    /// Używamy JsonElement, żeby uniknąć JsonException przy deserializacji.
    /// </summary>
    [JsonPropertyName("old_value")]
    public JsonElement? OldValue { get; init; }

    [JsonPropertyName("new_value")]
    public JsonElement? NewValue { get; init; }

    [JsonPropertyName("accepted")]
    public bool Accepted { get; init; }

    [JsonPropertyName("confidence")]
    public double? Confidence { get; init; }

    /// <summary>Normalizuje JsonElement (string/number/null) do czytelnego stringa.</summary>
    public static string Normalize(JsonElement? el) => el switch
    {
        null                                           => string.Empty,
        { ValueKind: JsonValueKind.Null }              => string.Empty,
        { ValueKind: JsonValueKind.String }            => el.Value.GetString() ?? string.Empty,
        { ValueKind: JsonValueKind.Number }            => el.Value.GetDouble().ToString("G"),
        { ValueKind: JsonValueKind.True  }             => "true",
        { ValueKind: JsonValueKind.False }             => "false",
        _                                              => el.Value.ToString(),
    };

    public string OldDisplay => Normalize(OldValue);
    public string NewDisplay => Normalize(NewValue);
}

public sealed class AnalysisItemApi
{
    [JsonPropertyName("track_id")]
    public int TrackId { get; init; }

    /// <summary>Klucz w API to "path", nie "track_path".</summary>
    [JsonPropertyName("path")]
    public string TrackPath { get; init; } = string.Empty;

    [JsonPropertyName("title")]
    public string Title { get; init; } = string.Empty;

    [JsonPropertyName("artist")]
    public string Artist { get; init; } = string.Empty;

    [JsonPropertyName("decisions")]
    public List<AnalysisDecisionApi> Decisions { get; init; } = [];

    [JsonPropertyName("provider_chain")]
    public string? ProviderChain { get; init; }

    [JsonPropertyName("confidence")]
    public double Confidence { get; init; }

    [JsonPropertyName("error")]
    public string? Error { get; init; }
}

public sealed class AnalysisJobStatus
{
    [JsonPropertyName("id")]
    public string Id { get; init; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; init; } = string.Empty;

    [JsonPropertyName("processed")]
    public int Processed { get; init; }

    [JsonPropertyName("total")]
    public int Total { get; init; }

    [JsonPropertyName("items")]
    public List<AnalysisItemApi> Items { get; init; } = [];
}

public sealed class AnalysisJobCreatedResponse
{
    [JsonPropertyName("job_id")]
    public string JobId { get; init; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; init; } = string.Empty;
}

public sealed class AnalysisApplyResponse
{
    [JsonPropertyName("updated_tracks")]
    public int UpdatedTracks { get; init; }

    [JsonPropertyName("applied_changes")]
    public int AppliedChanges { get; init; }
}
