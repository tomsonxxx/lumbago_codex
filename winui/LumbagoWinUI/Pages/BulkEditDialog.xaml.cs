using LumbagoWinUI.Models;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace LumbagoWinUI.Pages;

public sealed partial class BulkEditDialog : ContentDialog
{
    private readonly List<Track> _tracks;

    public BulkEditDialog(List<Track> tracks, XamlRoot xamlRoot)
    {
        InitializeComponent();

        _tracks = tracks;
        XamlRoot = xamlRoot;
        Title = $"Edycja zbiorcza — {tracks.Count} tracków";
        SubtitleLabel.Text =
            $"Zaznacz pola do zmiany. Niezaznaczone pola pozostają bez zmian. " +
            $"Dotyczy {tracks.Count} zaznaczonych tracków.";

        // Prefill where all tracks share the same value
        Prefill();

        // Validate on open
        UpdatePrimaryButton();
    }

    // ── Prefill wspólnych wartości ────────────────────────────────────────────

    private void Prefill()
    {
        PrefillText(TxtGenre, ChkGenre, _tracks.Select(t => t.Genre));
        PrefillText(TxtYear,  ChkYear,  _tracks.Select(t => t.Year));
        PrefillText(TxtKey,   ChkKey,   _tracks.Select(t => t.Key));
        PrefillText(TxtMood,  ChkMood,  _tracks.Select(t => t.Mood));
        PrefillText(TxtComment, ChkComment, _tracks.Select(t => t.Comment));

        var bpms = _tracks.Select(t => t.Bpm).Distinct().ToList();
        if (bpms.Count == 1 && bpms[0].HasValue)
            NumBpm.Value = bpms[0]!.Value;

        var energies = _tracks.Select(t => t.Energy).Distinct().ToList();
        if (energies.Count == 1 && energies[0].HasValue)
            SliderEnergy.Value = energies[0]!.Value;
    }

    private static void PrefillText(TextBox box, CheckBox chk, IEnumerable<string?> values)
    {
        var distinct = values.Distinct().ToList();
        if (distinct.Count == 1 && distinct[0] is not null)
        {
            box.Text = distinct[0]!;
            // Don't auto-check — user must explicitly opt in
        }
    }

    // ── Budowanie wynikowego TrackUpdate ─────────────────────────────────────

    public TrackUpdate BuildUpdate()
    {
        return new TrackUpdate
        {
            Genre   = ChkGenre.IsChecked   == true ? NullIfEmpty(TxtGenre.Text)   : Skip,
            Year    = ChkYear.IsChecked    == true ? NullIfEmpty(TxtYear.Text)    : Skip,
            Key     = ChkKey.IsChecked     == true ? NullIfEmpty(TxtKey.Text)     : Skip,
            Mood    = ChkMood.IsChecked    == true ? NullIfEmpty(TxtMood.Text)    : Skip,
            Comment = ChkComment.IsChecked == true ? NullIfEmpty(TxtComment.Text) : Skip,
            Bpm     = ChkBpm.IsChecked     == true && !double.IsNaN(NumBpm.Value)
                          ? NumBpm.Value : (double?)null,
            Energy  = ChkEnergy.IsChecked  == true ? SliderEnergy.Value : (double?)null,
        };
    }

    // Sentinel — wartość "nie zmieniaj" (null jest "wyczyść", Skip = pomijamy pole)
    // TrackUpdate pola są nullable — null oznacza wyczyść, brak ustawienia (Skip) = nie zmieniaj.
    // Używamy osobnej flagi IsFieldEnabled zamiast sentinel string.

    /// <summary>Zwraca true jeśli przynajmniej jedno pole jest zaznaczone.</summary>
    public bool HasAnyChange =>
        ChkGenre.IsChecked   == true ||
        ChkYear.IsChecked    == true ||
        ChkKey.IsChecked     == true ||
        ChkMood.IsChecked    == true ||
        ChkComment.IsChecked == true ||
        ChkBpm.IsChecked     == true ||
        ChkEnergy.IsChecked  == true;

    /// <summary>Mapa: field name → new value (tylko zaznaczone pola).</summary>
    public Dictionary<string, object?> GetChanges()
    {
        var changes = new Dictionary<string, object?>();
        if (ChkGenre.IsChecked   == true) changes["genre"]   = NullIfEmpty(TxtGenre.Text);
        if (ChkYear.IsChecked    == true) changes["year"]    = NullIfEmpty(TxtYear.Text);
        if (ChkKey.IsChecked     == true) changes["key"]     = NullIfEmpty(TxtKey.Text);
        if (ChkMood.IsChecked    == true) changes["mood"]    = NullIfEmpty(TxtMood.Text);
        if (ChkComment.IsChecked == true) changes["comment"] = NullIfEmpty(TxtComment.Text);
        if (ChkBpm.IsChecked     == true && !double.IsNaN(NumBpm.Value))
            changes["bpm"] = NumBpm.Value;
        if (ChkEnergy.IsChecked  == true)
            changes["energy"] = SliderEnergy.Value;
        return changes;
    }

    // ── Event handlers ────────────────────────────────────────────────────────

    private void Chk_Changed(object sender, RoutedEventArgs e)
    {
        // Włącz/wyłącz odpowiednie pole
        TxtGenre.IsEnabled    = ChkGenre.IsChecked    == true;
        TxtYear.IsEnabled     = ChkYear.IsChecked     == true;
        TxtKey.IsEnabled      = ChkKey.IsChecked      == true;
        TxtMood.IsEnabled     = ChkMood.IsChecked     == true;
        TxtComment.IsEnabled  = ChkComment.IsChecked  == true;
        NumBpm.IsEnabled      = ChkBpm.IsChecked      == true;
        SliderEnergy.IsEnabled = ChkEnergy.IsChecked  == true;

        UpdatePrimaryButton();
    }

    private void Txt_TextChanged(object sender, TextChangedEventArgs e) =>
        UpdatePrimaryButton();

    private void UpdatePrimaryButton()
    {
        IsPrimaryButtonEnabled = HasAnyChange;
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static string? NullIfEmpty(string? s) =>
        string.IsNullOrWhiteSpace(s) ? null : s.Trim();

    // Nie używamy sentinel — BuildUpdate nie ustawia pola gdy checkbox odznaczony.
    // Wywołujący sprawdza GetChanges() i tworzy PartialUpdate per pole.
    private const string? Skip = null;
}
