using System.Diagnostics;

namespace LumbagoWinUI.Services;

/// <summary>
/// Uruchamia serwer FastAPI (uvicorn) jako proces potomny i czeka na /health.
/// </summary>
public sealed class BackendLauncher : IDisposable
{
    private Process? _process;
    private readonly string _baseUrl;
    private readonly int _port;

    public BackendLauncher(string baseUrl = "http://127.0.0.1:8765")
    {
        _baseUrl = baseUrl;
        _port = int.Parse(new Uri(baseUrl).Port.ToString());
    }

    public async Task StartAsync(CancellationToken ct = default)
    {
        var (python, repoRoot) = FindPython();
        if (python is null)
            throw new InvalidOperationException(
                "Nie znaleziono interpretera Python. Zainstaluj Python 3.10+ i sprawdź PATH.");

        var psi = new ProcessStartInfo(python,
            $"-m uvicorn web.backend.api:app --host 127.0.0.1 --port {_port} --no-access-log")
        {
            WorkingDirectory = repoRoot,
            UseShellExecute = false,
            RedirectStandardOutput = false,
            RedirectStandardError = false,
            CreateNoWindow = true,
        };

        _process = Process.Start(psi)
            ?? throw new InvalidOperationException("Nie udało się uruchomić procesu Python.");

        await WaitForHealthAsync(ct);
    }

    private async Task WaitForHealthAsync(CancellationToken ct)
    {
        using var http = new System.Net.Http.HttpClient();
        var deadline = DateTime.UtcNow.AddSeconds(15);
        while (DateTime.UtcNow < deadline)
        {
            ct.ThrowIfCancellationRequested();
            try
            {
                var resp = await http.GetAsync($"{_baseUrl}/health", ct);
                if (resp.IsSuccessStatusCode) return;
            }
            catch { /* backend jeszcze nie gotowy */ }
            await Task.Delay(500, ct);
        }
        throw new TimeoutException("Backend FastAPI nie odpowiedział w ciągu 15 sekund.");
    }

    private static (string? python, string repoRoot) FindPython()
    {
        var exe = Environment.OSVersion.Platform == PlatformID.Win32NT ? "python.exe" : "python3";

        // Szukaj .venv względem katalogu wykonywalnego aplikacji (tj. repo root)
        var appDir = AppContext.BaseDirectory;
        // Idź w górę aż znajdziemy plik pyproject.toml lub requirements.txt
        var dir = new DirectoryInfo(appDir);
        while (dir is not null)
        {
            if (dir.GetFiles("pyproject.toml").Length > 0 ||
                dir.GetFiles("requirements.txt").Length > 0)
            {
                var venv = Path.Combine(dir.FullName, ".venv", "Scripts", exe);
                if (File.Exists(venv)) return (venv, dir.FullName);
                var venvUnix = Path.Combine(dir.FullName, ".venv", "bin", "python3");
                if (File.Exists(venvUnix)) return (venvUnix, dir.FullName);
                // Fallback: globalny python w tym repo rocie
                return (FindInPath(exe), dir.FullName);
            }
            dir = dir.Parent;
        }

        return (FindInPath(exe), appDir);
    }

    private static string? FindInPath(string exe)
    {
        var paths = Environment.GetEnvironmentVariable("PATH")?.Split(Path.PathSeparator) ?? [];
        foreach (var p in paths)
        {
            var full = Path.Combine(p, exe);
            if (File.Exists(full)) return full;
        }
        return null;
    }

    public void Dispose()
    {
        try
        {
            if (_process is { HasExited: false })
            {
                _process.Kill(entireProcessTree: true);
                _process.WaitForExit(3000);
            }
        }
        catch { /* ignoruj błędy przy zamknięciu */ }
        _process?.Dispose();
    }
}
