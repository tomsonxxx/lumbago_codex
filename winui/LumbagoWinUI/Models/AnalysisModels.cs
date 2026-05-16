using System.Text.Json.Serialization;

namespace LumbagoWinUI.Models;

public sealed class AnalysisDecisionApi
{
    [JsonPropertyName("field")]
    public string Field { get; init; } = string.Empty;

    [JsonPropertyName("old_value")]
    public string? OldValue { get; init; }

    [JsonPropertyName("new_value")]
    public string? NewValue { get; init; }

    [JsonPropertyName("accepted")]
    public bool Accepted { get; init; }

    [JsonPropertyName("confidence")]
    public double? Confidence { get; init; }
}

public sealed class AnalysisItemApi
{
    [JsonPropertyName("track_id")]
    public int TrackId { get; init; }

    [JsonPropertyName("track_path")]
    public string TrackPath { get; init; } = string.Empty;

    [JsonPropertyName("decisions")]
    public List<AnalysisDecisionApi> Decisions { get; init; } = [];

    [JsonPropertyName("provider_chain")]
    public string? ProviderChain { get; init; }

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
