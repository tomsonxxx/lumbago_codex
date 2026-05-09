using System.Text.Json.Serialization;

namespace LumbagoWinUI.Models;

/// <summary>
/// Payload do PUT /tracks/{path} — null = nie zmieniaj pola.
/// </summary>
public sealed class TrackUpdate
{
    [JsonPropertyName("title")]
    public string? Title { get; set; }

    [JsonPropertyName("artist")]
    public string? Artist { get; set; }

    [JsonPropertyName("album")]
    public string? Album { get; set; }

    [JsonPropertyName("albumartist")]
    public string? AlbumArtist { get; set; }

    [JsonPropertyName("year")]
    public string? Year { get; set; }

    [JsonPropertyName("genre")]
    public string? Genre { get; set; }

    [JsonPropertyName("tracknumber")]
    public string? TrackNumber { get; set; }

    [JsonPropertyName("composer")]
    public string? Composer { get; set; }

    [JsonPropertyName("comment")]
    public string? Comment { get; set; }

    [JsonPropertyName("publisher")]
    public string? Publisher { get; set; }

    [JsonPropertyName("bpm")]
    public double? Bpm { get; set; }

    [JsonPropertyName("key")]
    public string? Key { get; set; }

    [JsonPropertyName("mood")]
    public string? Mood { get; set; }

    [JsonPropertyName("energy")]
    public double? Energy { get; set; }
}
