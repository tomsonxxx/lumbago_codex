using LumbagoWinUI.Services;
using Microsoft.UI.Xaml;

namespace LumbagoWinUI;

public partial class App : Application
{
    public static ApiClient Api { get; private set; } = new();
    public static BackendLauncher? Backend { get; private set; }

    private MainWindow? _window;

    public App()
    {
        InitializeComponent();
    }

    protected override async void OnLaunched(LaunchActivatedEventArgs args)
    {
        Backend = new BackendLauncher();
        try
        {
            await Backend.StartAsync();
        }
        catch (Exception ex)
        {
            // Backend nie uruchomił się — pokazujemy okno z komunikatem błędu,
            // ale nie przerywamy pracy (część funkcji może działać offline)
            System.Diagnostics.Debug.WriteLine($"[BackendLauncher] {ex.Message}");
        }

        _window = new MainWindow();
        _window.Activate();
    }
}
