using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Windows.Storage;
using Windows.Storage.Pickers;

namespace LumbagoWinUI.Pages;

public sealed partial class ConverterPage : Page
{
    public ConverterPage()
    {
        InitializeComponent();
    }

    // ── Wybór pliku wejściowego ──────────────────────────────────────────────

    private async void BtnPickInput_Click(object sender, RoutedEventArgs e)
    {
        var picker = new FileOpenPicker();
        picker.FileTypeFilter.Add(".xml");

        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.Window);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);

        var file = await picker.PickSingleFileAsync();
        if (file is null) return;

        TxtInputPath.Text = file.Path;
        TxtTrackCount.Visibility = Visibility.Collapsed;
        UpdateConvertButton();
    }

    // ── Wybór pliku wyjściowego ──────────────────────────────────────────────

    private async void BtnPickOutput_Click(object sender, RoutedEventArgs e)
    {
        var picker = new FileSavePicker();
        picker.FileTypeChoices.Add("VirtualDJ XML", [".xml"]);
        picker.SuggestedFileName = "virtualdj_database";

        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.Window);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);

        var file = await picker.PickSaveFileAsync();
        if (file is null) return;

        TxtOutputPath.Text = file.Path;
        UpdateConvertButton();
    }

    // ── Konwersja ────────────────────────────────────────────────────────────

    private async void BtnConvert_Click(object sender, RoutedEventArgs e)
    {
        var input  = TxtInputPath.Text;
        var output = TxtOutputPath.Text;
        if (string.IsNullOrEmpty(input) || string.IsNullOrEmpty(output)) return;

        BtnConvert.IsEnabled = false;
        ConvertProgress.Visibility = Visibility.Visible;
        ShowStatus("Konwertowanie...", isError: false);

        try
        {
            var result = await App.Api.ConvertXmlAsync(input, output);
            ShowStatus(
                $"✓ Skonwertowano {result.Converted} tracków.\nZapisano: {result.OutputPath}",
                isError: false);
            TxtTrackCount.Text = $"Znaleziono {result.Converted} tracków w pliku wejściowym";
            TxtTrackCount.Visibility = Visibility.Visible;
        }
        catch (Exception ex)
        {
            ShowStatus($"Błąd konwersji: {ex.Message}", isError: true);
        }
        finally
        {
            BtnConvert.IsEnabled = true;
            ConvertProgress.Visibility = Visibility.Collapsed;
        }
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    private void UpdateConvertButton()
    {
        BtnConvert.IsEnabled =
            !string.IsNullOrEmpty(TxtInputPath.Text) &&
            !string.IsNullOrEmpty(TxtOutputPath.Text);
    }

    private void ShowStatus(string msg, bool isError)
    {
        ConvertStatus.Text = msg;
        ConvertStatus.Foreground = new Microsoft.UI.Xaml.Media.SolidColorBrush(
            isError
                ? Windows.UI.Color.FromArgb(255, 255, 107, 107)
                : Windows.UI.Color.FromArgb(255, 77, 255, 184));
        ConvertStatus.Visibility = Visibility.Visible;
    }
}
