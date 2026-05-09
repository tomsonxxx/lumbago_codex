using System.Collections.ObjectModel;
using LumbagoWinUI.Models;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;

namespace LumbagoWinUI.Pages;

public sealed partial class LibraryPage : Page
{
    private List<Track> _allTracks = [];
    public ObservableCollection<Track> FilteredTracks { get; } = [];

    public LibraryPage()
    {
        InitializeComponent();
    }

    protected override async void OnNavigatedTo(NavigationEventArgs e)
    {
        base.OnNavigatedTo(e);
        await LoadTracksAsync();
    }

    private async Task LoadTracksAsync()
    {
        ShowLoading(true);
        try
        {
            _allTracks = await App.Api.GetTracksAsync();
            ApplyFilter(SearchBox.Text);
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

    public void ApplySearch(string query) => ApplyFilter(query);

    private void ApplyFilter(string query)
    {
        FilteredTracks.Clear();
        var q = query?.Trim().ToLowerInvariant() ?? string.Empty;
        var results = string.IsNullOrEmpty(q)
            ? _allTracks
            : _allTracks.Where(t =>
                (t.Title?.ToLowerInvariant().Contains(q) ?? false) ||
                (t.Artist?.ToLowerInvariant().Contains(q) ?? false) ||
                (t.Album?.ToLowerInvariant().Contains(q) ?? false) ||
                (t.Genre?.ToLowerInvariant().Contains(q) ?? false));

        foreach (var t in results) FilteredTracks.Add(t);
        UpdateVisibility();
    }

    private void UpdateVisibility()
    {
        bool hasData = FilteredTracks.Count > 0;
        bool totalEmpty = _allTracks.Count == 0;

        LoadingPanel.Visibility = Microsoft.UI.Xaml.Visibility.Collapsed;
        EmptyPanel.Visibility = totalEmpty
            ? Microsoft.UI.Xaml.Visibility.Visible
            : Microsoft.UI.Xaml.Visibility.Collapsed;
        TrackListPanel.Visibility = hasData
            ? Microsoft.UI.Xaml.Visibility.Visible
            : Microsoft.UI.Xaml.Visibility.Collapsed;
    }

    private void ShowLoading(bool show)
    {
        LoadingPanel.Visibility = show
            ? Microsoft.UI.Xaml.Visibility.Visible
            : Microsoft.UI.Xaml.Visibility.Collapsed;
        TrackListPanel.Visibility = Microsoft.UI.Xaml.Visibility.Collapsed;
        EmptyPanel.Visibility = Microsoft.UI.Xaml.Visibility.Collapsed;
    }

    private void SearchBox_TextChanged(AutoSuggestBox sender, AutoSuggestBoxTextChangedEventArgs e)
    {
        if (e.Reason == AutoSuggestionBoxTextChangeReason.UserInput)
            ApplyFilter(sender.Text);
    }

    private async void BtnRefresh_Click(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        await LoadTracksAsync();
    }

    private void TrackList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (e.AddedItems.FirstOrDefault() is Track track)
        {
            // Window jest poza drzewem UIElement w WinUI 3 — używamy statycznej referencji.
            App.Window?.UpdatePlayerInfo(
                track.DisplayTitle, track.DisplayArtist, track.DisplayBpm, track.DisplayKey);
        }
    }
}
