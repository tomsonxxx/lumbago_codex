using System.Collections.ObjectModel;
using LumbagoWinUI.Models;
using Microsoft.UI;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Navigation;

namespace LumbagoWinUI.Pages;

public sealed partial class SmartTaggerPage : Page
{
    public ObservableCollection<TrackAnalysisViewModel> AnalysisItems { get; } = [];

    private string? _currentJobId;
    private DispatcherTimer? _pollTimer;

    public SmartTaggerPage()
    {
        InitializeComponent();
    }

    // ── Start analizy ────────────────────────────────────────────────────────

    private async void BtnRunTagger_Click(object sender, RoutedEventArgs e)
    {
        BtnRunTagger.IsEnabled = false;
        AnalysisItems.Clear();
        HideResults();
        ShowProgress("Uruchamianie analizy AI...", 0);

        try
        {
            _currentJobId = await App.Api.CreateAnalysisJobAsync();
        }
        catch (Exception ex)
        {
            BtnRunTagger.IsEnabled = true;
            HideProgress();
            ShowStatus($"Błąd uruchomienia: {ex.Message}", isError: true);
            return;
        }

        _pollTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(2) };
        _pollTimer.Tick += PollTimer_Tick;
        _pollTimer.Start();
    }

    // ── Polling statusu ──────────────────────────────────────────────────────

    private async void PollTimer_Tick(object? sender, object e)
    {
        if (_currentJobId is null) return;

        AnalysisJobStatus status;
        try
        {
            status = await App.Api.GetAnalysisJobAsync(_currentJobId);
        }
        catch
        {
            return;
        }

        var pct = status.Total > 0
            ? (double)status.Processed / status.Total * 100
            : 0;
        ShowProgress($"Analizuję tracki... ({status.Processed}/{status.Total})", pct);

        if (status.Status is "completed" or "failed")
        {
            _pollTimer?.Stop();
            _pollTimer = null;
            BtnRunTagger.IsEnabled = true;
            HideProgress();

            if (status.Status == "failed")
            {
                ShowStatus("Analiza zakończyła się błędem. Sprawdź klucze API w Ustawieniach lub logi serwera.", isError: true);
                return;
            }

            BuildResults(status);
        }
    }

    // ── Budowanie listy wyników ──────────────────────────────────────────────

    private void BuildResults(AnalysisJobStatus status)
    {
        AnalysisItems.Clear();

        int withChanges = 0;
        int totalDecisions = 0;

        foreach (var item in status.Items)
        {
            if (item.Decisions is null || item.Decisions.Count == 0) continue;

            var decisions = item.Decisions
                .Where(d => d.OldDisplay != d.NewDisplay)
                .Select(d => new DecisionViewModel
                {
                    Field      = d.Field,
                    OldDisplay = string.IsNullOrWhiteSpace(d.OldDisplay) ? "—" : d.OldDisplay,
                    NewDisplay = string.IsNullOrWhiteSpace(d.NewDisplay) ? "—" : d.NewDisplay,
                    Accepted   = true,
                })
                .ToList();

            if (decisions.Count == 0) continue;

            // Preferuj title/artist z API; fallback na nazwę pliku gdy brakuje metadanych
            var displayTitle = !string.IsNullOrWhiteSpace(item.Title) && !string.IsNullOrWhiteSpace(item.Artist)
                ? $"{item.Artist} — {item.Title}"
                : !string.IsNullOrWhiteSpace(item.Title)
                    ? item.Title
                    : System.IO.Path.GetFileNameWithoutExtension(item.TrackPath);

            var vm = new TrackAnalysisViewModel
            {
                TrackId      = item.TrackId,
                TrackPath    = item.TrackPath,
                TrackTitle   = displayTitle,
                ProviderBadge = item.ProviderChain is not null ? $"[{item.ProviderChain}]" : string.Empty,
            };
            foreach (var d in decisions) vm.Decisions.Add(d);

            AnalysisItems.Add(vm);
            withChanges++;
            totalDecisions += decisions.Count;
        }

        if (AnalysisItems.Count == 0)
        {
            ShowStatus(
                $"Analiza zakończona — brak nowych sugestii dla {status.Total} tracków. " +
                "Tagi są już kompletne lub AI nie znalazło dopasowań.",
                isError: false);
        }
        else
        {
            ShowStatus(
                $"Analiza zakończona: {withChanges} tracków z sugestiami, " +
                $"{totalDecisions} zmian do zaakceptowania.",
                isError: false);
            ShowResults();
            FooterPanel.Visibility    = Visibility.Visible;
            BtnAcceptAll.Visibility   = Visibility.Visible;
            BtnRejectAll.Visibility   = Visibility.Visible;
            FooterStatus.Text         = string.Empty;
        }
    }

    // ── Zaakceptuj/Odrzuć wszystkie ─────────────────────────────────────────

    private void BtnAcceptAll_Click(object sender, RoutedEventArgs e)
    {
        foreach (var vm in AnalysisItems)
            foreach (var d in vm.Decisions)
                d.Accepted = true;
    }

    private void BtnRejectAll_Click(object sender, RoutedEventArgs e)
    {
        foreach (var vm in AnalysisItems)
            foreach (var d in vm.Decisions)
                d.Accepted = false;
    }

    // ── Zastosuj zmiany ──────────────────────────────────────────────────────

    private async void BtnApply_Click(object sender, RoutedEventArgs e)
    {
        if (_currentJobId is null) return;

        var overrides = new Dictionary<string, Dictionary<string, bool>>();
        foreach (var vm in AnalysisItems)
        {
            var fieldOverrides = new Dictionary<string, bool>();
            foreach (var d in vm.Decisions)
                fieldOverrides[d.Field] = d.Accepted;
            overrides[vm.TrackId.ToString()] = fieldOverrides;
        }

        FooterStatus.Text = "Zapisywanie...";

        try
        {
            var result = await App.Api.ApplyAnalysisJobAsync(_currentJobId, overrides);
            FooterStatus.Text =
                $"✓ Zastosowano {result.AppliedChanges} zmian w {result.UpdatedTracks} trackach.";
            FooterStatus.Foreground =
                new SolidColorBrush(Windows.UI.Color.FromArgb(255, 77, 255, 184));

            BtnAcceptAll.Visibility = Visibility.Collapsed;
            BtnRejectAll.Visibility = Visibility.Collapsed;
        }
        catch (Exception ex)
        {
            FooterStatus.Text = $"Błąd zapisu: {ex.Message}";
            FooterStatus.Foreground =
                new SolidColorBrush(Windows.UI.Color.FromArgb(255, 255, 107, 107));
        }
    }

    // ── Helpers widoczności ──────────────────────────────────────────────────

    private void ShowProgress(string text, double pct)
    {
        ProgressPanel.Visibility  = Visibility.Visible;
        ProgressText.Text         = text;
        ProgressBar.Value         = pct;
        ProgressCount.Text        = pct > 0 ? $"{pct:F0}%" : string.Empty;
    }

    private void HideProgress() =>
        ProgressPanel.Visibility = Visibility.Collapsed;

    private void ShowStatus(string msg, bool isError)
    {
        StatusPanel.Visibility  = Visibility.Visible;
        StatusText.Text         = msg;
        StatusPanel.Background  = isError
            ? new SolidColorBrush(Windows.UI.Color.FromArgb(30, 255, 107, 107))
            : new SolidColorBrush(Windows.UI.Color.FromArgb(20, 77, 255, 184));
        StatusText.Foreground   = isError
            ? new SolidColorBrush(Windows.UI.Color.FromArgb(255, 255, 107, 107))
            : new SolidColorBrush(Windows.UI.Color.FromArgb(255, 77, 255, 184));
    }

    private void ShowResults() => ResultsPanel.Visibility = Visibility.Visible;

    private void HideResults()
    {
        ResultsPanel.Visibility  = Visibility.Collapsed;
        FooterPanel.Visibility   = Visibility.Collapsed;
        StatusPanel.Visibility   = Visibility.Collapsed;
        BtnAcceptAll.Visibility  = Visibility.Collapsed;
        BtnRejectAll.Visibility  = Visibility.Collapsed;
    }
}
