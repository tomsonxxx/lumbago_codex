using LumbagoWinUI.Models;
using LumbagoWinUI.Services;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace LumbagoWinUI.Pages;

public sealed partial class DuplicatesPage : Page
{
    public DuplicatesPage()
    {
        InitializeComponent();
    }

    private async void BtnAnalyze_Click(object sender, RoutedEventArgs e)
    {
        var mode = (ModeCombo.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "metadata";

        BtnAnalyze.IsEnabled = false;
        EmptyState.Visibility = Visibility.Collapsed;
        ShowStatus("Analizowanie biblioteki...", isError: false);

        // Wyczyść poprzednie wyniki (zostawiamy EmptyState na stosie)
        var toRemove = GroupsPanel.Children
            .OfType<Border>()
            .Where(b => b.Tag?.ToString() == "group")
            .ToList();
        foreach (var b in toRemove) GroupsPanel.Children.Remove(b);

        try
        {
            var result = await App.Api.AnalyzeDuplicatesAsync(mode);

            if (result.Groups.Count == 0)
            {
                EmptyState.Visibility = Visibility.Visible;
                ShowStatus("Nie znaleziono duplikatów.", isError: false);
            }
            else
            {
                ShowStatus($"Znaleziono {result.Groups.Count} grup(y) duplikatów.", isError: false);
                foreach (var group in result.Groups)
                    GroupsPanel.Children.Add(BuildGroupCard(group));
            }
        }
        catch (Exception ex)
        {
            EmptyState.Visibility = Visibility.Visible;
            ShowStatus($"Błąd analizy: {ex.Message}", isError: true);
        }
        finally
        {
            BtnAnalyze.IsEnabled = true;
        }
    }

    // ── Budowanie karty grupy duplikatów ─────────────────────────────────────

    private Border BuildGroupCard(DuplicateGroup group)
    {
        var card = new Border
        {
            Tag = "group",
            CornerRadius = new CornerRadius(12),
            BorderThickness = new Thickness(1),
            Padding = new Thickness(16),
            Margin = new Thickness(0, 0, 0, 4),
        };
        card.SetValue(Border.BackgroundProperty,
            App.Current.Resources["PanelBrush"] as Microsoft.UI.Xaml.Media.Brush);
        card.SetValue(Border.BorderBrushProperty,
            App.Current.Resources["StrokeBrush"] as Microsoft.UI.Xaml.Media.Brush);

        var panel = new StackPanel { Spacing = 10 };

        // Nagłówek grupy
        var header = new Grid();
        header.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        header.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var sim = (int)(group.Similarity * 100);
        var headerText = new TextBlock
        {
            Text = $"{group.Tracks.Count} kopie · podobieństwo {sim}%",
            Foreground = App.Current.Resources["AccentWarningBrush"] as Microsoft.UI.Xaml.Media.Brush,
        };
        headerText.Style = App.Current.Resources["SectionText"] as Style;
        Grid.SetColumn(headerText, 0);
        header.Children.Add(headerText);
        panel.Children.Add(header);

        // Wiersze tracków
        foreach (var track in group.Tracks)
        {
            var row = new Grid { Margin = new Thickness(0, 2, 0, 2) };
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(80, GridUnitType.Pixel) });
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var info = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
            info.Children.Add(new TextBlock
            {
                Text = track.DisplayTitle,
                TextTrimming = Microsoft.UI.Xaml.TextTrimming.CharacterEllipsis,
                Style = App.Current.Resources["BodyText"] as Style,
            });
            info.Children.Add(new TextBlock
            {
                Text = track.Path,
                TextTrimming = Microsoft.UI.Xaml.TextTrimming.CharacterEllipsis,
                Style = App.Current.Resources["CaptionText"] as Style,
            });
            Grid.SetColumn(info, 0);

            var dur = new TextBlock
            {
                Text = track.DisplayDuration,
                VerticalAlignment = VerticalAlignment.Center,
                HorizontalAlignment = HorizontalAlignment.Center,
                Style = App.Current.Resources["CaptionText"] as Style,
            };
            Grid.SetColumn(dur, 1);

            var delBtn = new Button
            {
                Content = "Usuń z biblioteki",
                Tag = track.Path,
                VerticalAlignment = VerticalAlignment.Center,
            };
            delBtn.Style = App.Current.Resources["DangerButton"] as Style;
            delBtn.Click += async (s, _) => await DeleteTrack(s as Button, row, group);
            Grid.SetColumn(delBtn, 2);

            row.Children.Add(info);
            row.Children.Add(dur);
            row.Children.Add(delBtn);
            panel.Children.Add(row);

            // Separator
            if (track != group.Tracks.Last())
                panel.Children.Add(new Border
                {
                    Height = 1,
                    Margin = new Thickness(0, 4, 0, 4),
                    Background = App.Current.Resources["StrokeBrush"] as Microsoft.UI.Xaml.Media.Brush,
                });
        }

        card.Child = panel;
        return card;
    }

    // ── Usuwanie tracka ──────────────────────────────────────────────────────

    private async Task DeleteTrack(Button? btn, Grid row, DuplicateGroup group)
    {
        if (btn?.Tag is not string path) return;

        var dlg = new ContentDialog
        {
            Title = "Usuń z biblioteki",
            Content = $"Usunąć \"{System.IO.Path.GetFileName(path)}\" z bazy?\nPlik na dysku pozostanie.",
            PrimaryButtonText = "Usuń",
            CloseButtonText = "Anuluj",
            XamlRoot = XamlRoot,
        };
        if (await dlg.ShowAsync() != ContentDialogResult.Primary) return;

        btn.IsEnabled = false;
        try
        {
            await App.Api.DeleteTrackAsync(path);
            // Wyciemnij wiersz
            row.Opacity = 0.35;
            row.IsHitTestVisible = false;
            ShowStatus($"Usunięto: {System.IO.Path.GetFileName(path)}", isError: false);
        }
        catch (Exception ex)
        {
            btn.IsEnabled = true;
            ShowStatus($"Błąd usuwania: {ex.Message}", isError: true);
        }
    }

    // ── Status ───────────────────────────────────────────────────────────────

    private void ShowStatus(string msg, bool isError)
    {
        StatusMsg.Text = msg;
        StatusMsg.Foreground = new Microsoft.UI.Xaml.Media.SolidColorBrush(
            isError
                ? Windows.UI.Color.FromArgb(255, 255, 107, 107)
                : Windows.UI.Color.FromArgb(255, 168, 179, 199));
        StatusMsg.Visibility = Visibility.Visible;
    }
}
