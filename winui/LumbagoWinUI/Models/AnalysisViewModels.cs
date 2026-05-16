using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace LumbagoWinUI.Models;

public sealed class DecisionViewModel : INotifyPropertyChanged
{
    public string Field { get; init; } = string.Empty;
    public string OldDisplay { get; init; } = "—";
    public string NewDisplay { get; init; } = "—";

    public string FieldDisplay => s_fieldLabels.TryGetValue(Field, out var label) ? label : Field;

    private bool _accepted;
    public bool Accepted
    {
        get => _accepted;
        set
        {
            if (_accepted != value)
            {
                _accepted = value;
                OnPropertyChanged();
            }
        }
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    private void OnPropertyChanged([CallerMemberName] string? name = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));

    private static readonly Dictionary<string, string> s_fieldLabels = new()
    {
        ["title"]    = "Tytuł",
        ["artist"]   = "Artysta",
        ["album"]    = "Album",
        ["genre"]    = "Gatunek",
        ["year"]     = "Rok",
        ["bpm"]      = "BPM",
        ["key"]      = "Tonacja",
        ["mood"]     = "Nastrój",
        ["energy"]   = "Energia",
        ["comment"]  = "Komentarz",
    };
}

public sealed class TrackAnalysisViewModel
{
    public int TrackId { get; init; }
    public string TrackPath { get; init; } = string.Empty;
    public string TrackTitle { get; init; } = string.Empty;
    public string ProviderBadge { get; init; } = string.Empty;
    public ObservableCollection<DecisionViewModel> Decisions { get; init; } = [];
}
