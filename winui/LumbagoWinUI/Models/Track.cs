using System.Text.Json.Serialization;

namespace LumbagoWinUI.Models;

public sealed class Track
{
    [JsonPropertyName("id")]
    public int Id { get; init; }

    [JsonPropertyName("path")]
    public string Path { get; init; } = string.Empty;

    [JsonPropertyName("title")]
    public string? Title { get; init; }

    [JsonPropertyName("artist")]
    public string? Artist { get; init; }

    [JsonPropertyName("album")]
    public string? Album { get; init; }

    [JsonPropertyName("albumartist")]
    public string? AlbumArtist { get; init; }

    [JsonPropertyName("year")]
    public string? Year { get; init; }

    [JsonPropertyName("genre")]
    public string? Genre { get; init; }

    [JsonPropertyName("tracknumber")]
    public string? TrackNumber { get; init; }

    [JsonPropertyName("bpm")]
    public double? Bpm { get; init; }

    [JsonPropertyName("key")]
    public string? Key { get; init; }

    [JsonPropertyName("loudness")]
    public double? Loudness { get; init; }

    [JsonPropertyName("duration")]
    public double? Duration { get; init; }

    [JsonPropertyName("file_size")]
    public long? FileSize { get; init; }

    [JsonPropertyName("format")]
    public string? Format { get; init; }

    [JsonPropertyName("bitrate")]
    public int? Bitrate { get; init; }

    [JsonPropertyName("energy")]
    public double? Energy { get; init; }

    [JsonPropertyName("mood")]
    public string? Mood { get; init; }

    [JsonPropertyName("comment")]
    public string? Comment { get; init; }

    [JsonPropertyName("artwork_path")]
    public string? ArtworkPath { get; init; }

    [JsonPropertyName("date_added")]
    public DateTimeOffset? DateAdded { get; init; }

    [JsonPropertyName("tags")]
    public List<string> Tags { get; init; } = [];

    // Computed display helpers
    public string DisplayTitle => Title ?? System.IO.Path.GetFileNameWithoutExtension(Path);
    public string DisplayArtist => Artist ?? "—";
    public string DisplayAlbum => Album ?? "—";
    public string DisplayBpm => Bpm.HasValue ? $"{Bpm:F0}" : "—";
    public string DisplayKey => Key ?? "—";
    public string DisplayDuration => Duration.HasValue
        ? TimeSpan.FromSeconds(Duration.Value).ToString(@"m\:ss")
        : "—";
}
