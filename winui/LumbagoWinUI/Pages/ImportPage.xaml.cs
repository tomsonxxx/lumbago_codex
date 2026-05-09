using System.Collections.ObjectModel;
using LumbagoWinUI.Models;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Windows.Storage.Pickers;

namespace LumbagoWinUI.Pages;

public sealed partial class ImportPage : Page
{
    private readonly ObservableCollection<Track> _previewTracks = [];

    public ImportPage()
    {
        InitializeComponent();
        PreviewList.ItemsSource = _previewTracks;
    }

    // ── Wybór folderu ────────────────────────────────────────────────────────

    private async void BtnBrowse_Click(object sender, RoutedEventArgs e)
    {
        var picker = new FolderPicker();
        picker.FileTypeFilter.Add("*");

        // WinUI 3 unpackaged: inicjalizacja pickera przez HWND okna
        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.Window);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);

        var folder = await picker.PickSingleFolderAsync();
        if (folder is null) return;

        TxtFolder.Text = folder.Path;
        BtnScan.IsEnabled = true;
        BtnImport.IsEnabled = false;
        _previewTracks.Clear();
        SetPreviewVisible(false);
        HideStatus();
    }

    // ── Skanowanie podglądu ──────────────────────────────────────────────────

    private async void BtnScan_Click(object sender, RoutedEventArgs e)
    {
        var folder = TxtFolder.Text;
        if (string.IsNullOrEmpty(folder)) return;

        BtnScan.IsEnabled = false;
        BtnImport.IsEnabled = false;
        ShowScanStatus("Skanowanie folderu...", isError: false);
        _previewTracks.Clear();
        SetPreviewVisible(false);

        try
        {
            var result = await App.Api.ImportPreviewAsync(
                folder, ChkRecursive.IsChecked == true);

            foreach (var t in result.Tracks) _previewTracks.Add(t);

            SetPreviewVisible(true);
            PreviewList.SelectAll();

            var msg = $"Znaleziono {result.Tracks.Count} plik(ów).";
            if (result.Errors.Count > 0) msg += $" Błędy skanowania: {result.Errors.Count}";
            ShowScanStatus(msg, isError: false);

            BtnImport.IsEnabled = result.Tracks.Count > 0;
        }
        catch (Exception ex)
        {
            ShowScanStatus($"Błąd skanowania: {ex.Message}", isError: true);
        }
        finally
        {
            BtnScan.IsEnabled = true;
        }
    }

    // ── Import ───────────────────────────────────────────────────────────────

    private async void BtnImport_Click(object sender, RoutedEventArgs e)
    {
        var selected = PreviewList.SelectedItems
            .OfType<Track>()
            .Select(t => t.Path)
            .ToList();

        if (selected.Count == 0)
        {
            ShowImportStatus("Zaznacz co najmniej jeden utwór.", isError: true);
            return;
        }

        BtnImport.IsEnabled = false;
        BtnScan.IsEnabled   = false;
        ImportProgress.Visibility = Visibility.Visible;
        ShowImportStatus($"Importowanie {selected.Count} plik(ów)...", isError: false);

        try
        {
            var result = await App.Api.ImportCommitAsync(selected);
            var msg = $"✓ Zaimportowano {result.Imported} utwór(y).";
            if (result.Errors.Count > 0) msg += $" Błędy: {result.Errors.Count}";
            ShowImportStatus(msg, isError: false);

            // Usuń zaimportowane z podglądu
            var done = selected.ToHashSet();
            foreach (var t in _previewTracks.Where(t => done.Contains(t.Path)).ToList())
                _previewTracks.Remove(t);

            if (_previewTracks.Count == 0)
                SetPreviewVisible(false);
            else
                TxtPreviewCount.Text = $"{_previewTracks.Count} plików pozostało";
        }
        catch (Exception ex)
        {
            ShowImportStatus($"Błąd importu: {ex.Message}", isError: true);
        }
        finally
        {
            BtnImport.IsEnabled = _previewTracks.Count > 0;
            BtnScan.IsEnabled   = true;
            ImportProgress.Visibility = Visibility.Collapsed;
        }
    }

    // ── Zaznaczanie ──────────────────────────────────────────────────────────

    private void BtnSelectAll_Click(object sender, RoutedEventArgs e) =>
        PreviewList.SelectAll();

    private void BtnDeselectAll_Click(object sender, RoutedEventArgs e) =>
        PreviewList.DeselectRange(
            new Microsoft.UI.Xaml.Data.ItemIndexRange(0, (uint)_previewTracks.Count));

    // ── Helpers UI ───────────────────────────────────────────────────────────

    private void SetPreviewVisible(bool visible)
    {
        var v = visible ? Visibility.Visible : Visibility.Collapsed;
        PreviewList.Visibility    = v;
        PreviewToolbar.Visibility = v;
        if (visible) TxtPreviewCount.Text = $"{_previewTracks.Count} plików gotowych do importu";
    }

    private void ShowScanStatus(string msg, bool isError)
    {
        ScanStatus.Text       = msg;
        ScanStatus.Foreground = MakeBrush(isError);
        ScanStatus.Visibility = Visibility.Visible;
    }

    private void ShowImportStatus(string msg, bool isError)
    {
        ImportStatus.Text       = msg;
        ImportStatus.Foreground = MakeBrush(isError);
        ImportStatus.Visibility = Visibility.Visible;
    }

    private void HideStatus()
    {
        ScanStatus.Visibility   = Visibility.Collapsed;
        ImportStatus.Visibility = Visibility.Collapsed;
    }

    private static Microsoft.UI.Xaml.Media.SolidColorBrush MakeBrush(bool isError) =>
        new(isError
            ? Windows.UI.Color.FromArgb(255, 255, 107, 107)
            : Windows.UI.Color.FromArgb(255, 168, 179, 199));
}
