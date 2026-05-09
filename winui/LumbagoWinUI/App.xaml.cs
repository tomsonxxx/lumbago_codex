using LumbagoWinUI.Services;
using Microsoft.UI.Xaml;

namespace LumbagoWinUI;

public partial class App : Application
{
    public static ApiClient Api { get; private set; } = new();
    public static BackendLauncher? Backend { get; private set; }

    /// <summary>
    /// Statyczna referencja do głównego okna — potrzebna bo Window nie jest UIElement
    /// i nie wchodzi do drzewa wizualnego WinUI 3.
    /// </summary>
    public static MainWindow? Window { get; private set; }

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
        Window = _window;
        _window.Closed += OnMainWindowClosed;
        _window.Activate();
    }

    private void OnMainWindowClosed(object sender, Microsoft.UI.Xaml.WindowEventArgs args)
    {
        Backend?.Dispose();
        Backend = null;
        Window = null;
    }
}
