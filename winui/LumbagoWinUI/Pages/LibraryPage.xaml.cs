using System.Collections.ObjectModel;
using LumbagoWinUI.Models;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Navigation;

namespace LumbagoWinUI.Pages;

public sealed partial class LibraryPage : Page
{
    private List<Track> _allTracks = [];
    public ObservableCollection<Track> FilteredTracks { get; } = [];

    private Track? _selectedTrack;
    private bool _isGridView;

    public LibraryPage()
    {
        InitializeComponent();
    }

    protected override async void OnNavigatedTo(NavigationEventArgs e)
    {
        base.OnNavigatedTo(e);
        await LoadTracksAsync();
    }

    // ── Ładowanie danych ────────────────────────────────────────────────────

    private async Task LoadTracksAsync()
    {
        ShowLoading(true);
        try
        {
            _allTracks = await App.Api.GetTracksAsync();
            ApplyAllFilters();
        }
        catch (Exception ex)
        {
            ShowLoading(false);
            var dlg = new ContentDialog
            {
                Title = "Błąd połączenia",
                Content = $"Nie udało się pobrać tracków.\n\n{ex.Message}",
                CloseButtonText = "OK",
                XamlRoot = XamlRoot,
            };
            await dlg.ShowAsync();
            return;
        }
        ShowLoading(false);
        UpdateVisibility();
    }

    // ── Filtrowanie ─────────────────────────────────────────────────────────

    public void ApplySearch(string query)
    {
        SearchBox.Text = query;
        ApplyAllFilters();
    }

    private void ApplyAllFilters()
    {
        var q = SearchBox.Text?.Trim().ToLowerInvariant() ?? string.Empty;
        var genre = FilterGenre.Text?.Trim().ToLowerInvariant() ?? string.Empty;
        var key = (FilterKey.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? string.Empty;
        var bpmMin = double.IsNaN(FilterBpmMin.Value) ? 0 : FilterBpmMin.Value;
        var bpmMax = double.IsNaN(FilterBpmMax.Value) ? double.MaxValue : FilterBpmMax.Value;

        FilteredTracks.Clear();
        foreach (var t in _allTracks)
        {
            // Tekst (tytuł/artysta/album/gatunek)
            if (!string.IsNullOrEmpty(q) &&
                !(t.Title?.ToLowerInvariant().Contains(q) ?? false) &&
                !(t.Artist?.ToLowerInvariant().Contains(q) ?? false) &&
                !(t.Album?.ToLowerInvariant().Contains(q) ?? false) &&
                !(t.Genre?.ToLowerInvariant().Contains(q) ?? false))
                continue;

            // Gatunek
            if (!string.IsNullOrEmpty(genre) &&
                !(t.Genre?.ToLowerInvariant().Contains(genre) ?? false))
                continue;

            // Tonacja (Camelot)
            if (!string.IsNullOrEmpty(key) &&
                !string.Equals(t.Key, key, StringComparison.OrdinalIgnoreCase))
                continue;

            // BPM min
            if (t.Bpm.HasValue && t.Bpm.Value < bpmMin) continue;

            // BPM max
            if (t.Bpm.HasValue && bpmMax < double.MaxValue && t.Bpm.Value > bpmMax) continue;

            FilteredTracks.Add(t);
        }
        UpdateVisibility();
    }

    // ── Widoczność paneli ───────────────────────────────────────────────────

    private void ShowLoading(bool show)
    {
        LoadingPanel.Visibility   = show ? Visibility.Visible : Visibility.Collapsed;
        TrackListPanel.Visibility = Visibility.Collapsed;
        TrackGrid.Visibility      = Visibility.Collapsed;
        EmptyPanel.Visibility     = Visibility.Collapsed;
    }

    private void UpdateVisibility()
    {
        bool hasData   = FilteredTracks.Count > 0;
        bool totalEmpty = _allTracks.Count == 0;

        LoadingPanel.Visibility = Visibility.Collapsed;

        if (totalEmpty)
        {
            EmptyPanel.Visibility     = Visibility.Visible;
            TrackListPanel.Visibility = Visibility.Collapsed;
            TrackGrid.Visibility      = Visibility.Collapsed;
        }
        else if (hasData)
        {
            EmptyPanel.Visibility     = Visibility.Collapsed;
            TrackListPanel.Visibility = _isGridView ? Visibility.Collapsed : Visibility.Visible;
            TrackGrid.Visibility      = _isGridView ? Visibility.Visible   : Visibility.Collapsed;
        }
        else
        {
            // Filtry dały 0 wyników, ale baza nie jest pusta
            EmptyPanel.Visibility     = Visibility.Collapsed;
            TrackListPanel.Visibility = _isGridView ? Visibility.Collapsed : Visibility.Visible;
            TrackGrid.Visibility      = _isGridView ? Visibility.Visible   : Visibility.Collapsed;
        }
    }

    // ── Zaznaczenie tracka ───────────────────────────────────────────────────

    private void TrackList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (e.AddedItems.FirstOrDefault() is Track t) SelectTrack(t);
    }

    private void TrackGrid_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (e.AddedItems.FirstOrDefault() is Track t) SelectTrack(t);
    }

    private void TrackList_DoubleTapped(object sender, DoubleTappedRoutedEventArgs e)
    {
        if (_selectedTrack is not null) PlayTrackFromLibrary(_selectedTrack);
    }

    private void SelectTrack(Track track)
    {
        _selectedTrack = track;
        FillDetailPanel(track);
        DetailPanel.Visibility = Visibility.Visible;

        App.Window?.UpdatePlayerInfo(
            track.DisplayTitle, track.DisplayArtist, track.DisplayBpm, track.DisplayKey);
    }

    /// <summary>Wołana z LibraryPage (double-click) lub z MainWindow (BtnPlay bez aktywnego tracka).</summary>
    public void PlayFirstTrack()
    {
        var list = FilteredTracks.ToList();
        if (list.Count == 0) return;
        var track = list[0];
        SelectTrack(track);
        App.Window?.PlayTrack(track, list, 0);
    }

    public void PlayTrackFromLibrary(Track track)
    {
        var list = FilteredTracks.ToList();
        var idx = list.IndexOf(track);
        SelectTrack(track);
        App.Window?.PlayTrack(track, list, idx >= 0 ? idx : 0);
    }

    // ── Panel szczegółów ────────────────────────────────────────────────────

    private void FillDetailPanel(Track t)
    {
        DetailTitle.Text       = t.Title ?? string.Empty;
        DetailArtist.Text      = t.Artist ?? string.Empty;
        DetailAlbum.Text       = t.Album ?? string.Empty;
        DetailBpm.Text         = t.Bpm.HasValue ? $"{t.Bpm:F1}" : string.Empty;
        DetailKey.Text         = t.Key ?? string.Empty;
        DetailGenre.Text       = t.Genre ?? string.Empty;
        DetailYear.Text        = t.Year ?? string.Empty;
        DetailTrackNumber.Text = t.TrackNumber ?? string.Empty;
        DetailComment.Text     = t.Comment ?? string.Empty;

        DetailDuration.Text = t.DisplayDuration;
        DetailFormat.Text   = t.Format?.ToUpperInvariant() ?? "—";
        DetailBitrate.Text  = t.Bitrate.HasValue ? $"{t.Bitrate} kbps" : "—";
        DetailPath.Text     = t.Path;

        HideDetailStatus();
    }

    private async void BtnDetailSave_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedTrack is null) return;

        BtnDetailSave.IsEnabled = false;
        ShowDetailStatus("Zapisywanie...", isError: false);
        try
        {
            var update = new TrackUpdate
            {
                Title       = NullIfEmpty(DetailTitle.Text),
                Artist      = NullIfEmpty(DetailArtist.Text),
                Album       = NullIfEmpty(DetailAlbum.Text),
                Genre       = NullIfEmpty(DetailGenre.Text),
                Year        = NullIfEmpty(DetailYear.Text),
                TrackNumber = NullIfEmpty(DetailTrackNumber.Text),
                Comment     = NullIfEmpty(DetailComment.Text),
                Key         = NullIfEmpty(DetailKey.Text),
                Bpm         = double.TryParse(DetailBpm.Text, out var bpm) ? bpm : null,
            };

            var updated = await App.Api.UpdateTrackAsync(_selectedTrack.Path, update);
            if (updated is not null)
            {
                // Zastąp w _allTracks, a potem przelicz filtry — edytowane pole (gatunek,
                // tonacja, BPM) mogło zmienić widoczność tracka w bieżącym widoku.
                var idx = _allTracks.FindIndex(t => t.Path == updated.Path);
                if (idx >= 0) _allTracks[idx] = updated;

                _selectedTrack = updated;
                FillDetailPanel(updated);
                App.Window?.UpdatePlayerInfo(
                    updated.DisplayTitle, updated.DisplayArtist, updated.DisplayBpm, updated.DisplayKey);

                // Przebuduj FilteredTracks z uwzględnieniem aktualnych filtrów.
                ApplyAllFilters();
            }
            ShowDetailStatus("✓ Zapisano", isError: false);
        }
        catch (Exception ex)
        {
            ShowDetailStatus($"Błąd: {ex.Message}", isError: true);
        }
        finally
        {
            BtnDetailSave.IsEnabled = true;
        }
    }

    private void BtnDetailReset_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedTrack is not null) FillDetailPanel(_selectedTrack);
    }

    private void ShowDetailStatus(string msg, bool isError)
    {
        DetailStatus.Text = msg;
        DetailStatus.Foreground = isError
            ? new Microsoft.UI.Xaml.Media.SolidColorBrush(Windows.UI.Color.FromArgb(255, 255, 107, 107))
            : new Microsoft.UI.Xaml.Media.SolidColorBrush(Windows.UI.Color.FromArgb(255, 77, 255, 184));
        DetailStatus.Visibility = Visibility.Visible;
    }

    private void HideDetailStatus() => DetailStatus.Visibility = Visibility.Collapsed;

    private static string? NullIfEmpty(string? s) =>
        string.IsNullOrWhiteSpace(s) ? null : s.Trim();

    // ── Toolbar — eventy ─────────────────────────────────────────────────────

    private async void BtnRefresh_Click(object sender, RoutedEventArgs e)
    {
        _selectedTrack = null;
        DetailPanel.Visibility = Visibility.Collapsed;
        await LoadTracksAsync();
    }

    private void BtnGoImport_Click(object sender, RoutedEventArgs e) =>
        App.Window?.NavigateTo("Import");

    private void BtnFilter_Checked(object sender, RoutedEventArgs e) =>
        FilterPanel.Visibility = Visibility.Visible;

    private void BtnFilter_Unchecked(object sender, RoutedEventArgs e) =>
        FilterPanel.Visibility = Visibility.Collapsed;

    private void BtnGridView_Checked(object sender, RoutedEventArgs e)
    {
        _isGridView = true;
        UpdateVisibility();
    }

    private void BtnGridView_Unchecked(object sender, RoutedEventArgs e)
    {
        _isGridView = false;
        UpdateVisibility();
    }

    private void BtnClearFilters_Click(object sender, RoutedEventArgs e)
    {
        FilterGenre.Text = string.Empty;
        FilterKey.SelectedIndex = 0;
        FilterBpmMin.Value = double.NaN;
        FilterBpmMax.Value = double.NaN;
        ApplyAllFilters();
    }

    // ── Filter eventy ───────────────────────────────────────────────────────

    private void SearchBox_TextChanged(AutoSuggestBox sender, AutoSuggestBoxTextChangedEventArgs e)
    {
        if (e.Reason == AutoSuggestionBoxTextChangeReason.UserInput) ApplyAllFilters();
    }

    private void FilterGenre_TextChanged(object sender, TextChangedEventArgs e) => ApplyAllFilters();

    private void FilterKey_SelectionChanged(object sender, SelectionChangedEventArgs e) => ApplyAllFilters();

    private void FilterBpm_Changed(NumberBox sender, NumberBoxValueChangedEventArgs e) =>
        ApplyAllFilters();
}
