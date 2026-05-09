using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;

namespace LumbagoWinUI.Pages;

public sealed partial class SettingsPage : Page
{
    private static readonly (string Key, Func<SettingsPage, string> Getter, Action<SettingsPage, string> Setter)[] _fields =
    [
        ("openai_api_key",   p => p.TxtOpenAi.Password,  (p, v) => p.TxtOpenAi.Password  = v),
        ("grok_api_key",     p => p.TxtGrok.Password,    (p, v) => p.TxtGrok.Password    = v),
        ("gemini_api_key",   p => p.TxtGemini.Password,  (p, v) => p.TxtGemini.Password  = v),
        ("deepseek_api_key", p => p.TxtDeepSeek.Password,(p, v) => p.TxtDeepSeek.Password= v),
        ("acoustid_api_key", p => p.TxtAcoustId.Text,    (p, v) => p.TxtAcoustId.Text    = v),
        ("discogs_token",    p => p.TxtDiscogs.Password, (p, v) => p.TxtDiscogs.Password = v),
    ];

    public SettingsPage()
    {
        InitializeComponent();
    }

    protected override async void OnNavigatedTo(NavigationEventArgs e)
    {
        base.OnNavigatedTo(e);
        await LoadSettingsAsync();
    }

    private async Task LoadSettingsAsync()
    {
        BtnSave.IsEnabled = false;
        try
        {
            foreach (var (key, _, setter) in _fields)
            {
                var value = await App.Api.GetSettingAsync(key);
                if (value is not null) setter(this, value);
            }
        }
        catch
        {
            // backend niedostępny — pola zostają puste
        }
        finally { BtnSave.IsEnabled = true; }
    }

    private async void BtnSave_Click(object sender, RoutedEventArgs e)
    {
        BtnSave.IsEnabled = false;
        StatusMsg.Visibility = Visibility.Collapsed;
        try
        {
            foreach (var (key, getter, _) in _fields)
            {
                // Save all values, including empty strings — allows users to clear a stored key.
                var value = getter(this);
                await App.Api.SetSettingAsync(key, value);
            }
            StatusMsg.Text = "✓ Ustawienia zapisane";
            StatusMsg.Visibility = Visibility.Visible;
        }
        catch (Exception ex)
        {
            StatusMsg.Text = $"Błąd: {ex.Message}";
            StatusMsg.Foreground = new Microsoft.UI.Xaml.Media.SolidColorBrush(
                Windows.UI.Color.FromArgb(255, 255, 107, 107));
            StatusMsg.Visibility = Visibility.Visible;
        }
        finally { BtnSave.IsEnabled = true; }
    }

    private void BtnCancel_Click(object sender, RoutedEventArgs e)
    {
        Frame.GoBack();
    }
}
