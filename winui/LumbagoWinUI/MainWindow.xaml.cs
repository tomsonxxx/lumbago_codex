using LumbagoWinUI.Models;
using LumbagoWinUI.Pages;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Windows.Media.Core;
using Windows.Media.Playback;

namespace LumbagoWinUI;

public sealed partial class MainWindow : Window
{
    private static readonly Dictionary<string, Type> _pages = new()
    {
        ["Start"]        = typeof(StartPage),
        ["Library"]      = typeof(LibraryPage),
        ["Import"]       = typeof(ImportPage),
        ["Duplicates"]   = typeof(DuplicatesPage),
        ["Converter"]    = typeof(ConverterPage),
        ["Settings"]     = typeof(SettingsPage),
        ["SmartTagger"]  = typeof(SmartTaggerPage),
    };

    // Guard: prevents SelectionChanged from re-triggering Navigate when
    // we programmatically set SelectedItem inside SelectNavItem().
    private bool _suppressNavigation;

    // ── Odtwarzacz ──────────────────────────────────────────────────────────
    private readonly MediaPlayer _player = new();
    private DispatcherTimer? _positionTimer;
    private Track? _currentTrack;

    // Lista tracków dostępna dla przeskakiwania prev/next
    private List<Track> _playerQueue = [];
    private int _playerQueueIndex = -1;

    // Czy użytkownik aktualnie ciągnie suwak seek (żeby nie aktualizować pozycji z timera)
    private bool _isSeeking;

    public MainWindow()
    {
        InitializeComponent();
        ExtendsContentIntoTitleBar = true;
        InitPlayer();
        Navigate("Library");
        SelectNavItem("Library");
    }

    // ── Inicjalizacja playera ────────────────────────────────────────────────

    private void InitPlayer()
    {
        _player.PlaybackSession.PlaybackStateChanged += PlaybackSession_StateChanged;
        _player.PlaybackSession.NaturalDurationChanged += PlaybackSession_DurationChanged;
        _player.MediaEnded += Player_MediaEnded;

        _positionTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(500) };
        _positionTimer.Tick += PositionTimer_Tick;
        _positionTimer.Start();
    }

    // ── Publiczny API dla stron ──────────────────────────────────────────────

    public void UpdatePlayerInfo(string title, string artist, string bpm, string key)
    {
        PlayerTitle.Text = title;
        PlayerArtist.Text = artist;
        PlayerBpm.Text = string.IsNullOrEmpty(bpm) ? "— BPM" : $"{bpm} BPM";
        PlayerKey.Text = string.IsNullOrEmpty(key) ? "—" : key;
    }

    /// <summary>Odtwarza podany track. Może być wołane z LibraryPage po podwójnym kliknięciu lub zaznaczeniu.</summary>
    public void PlayTrack(Track track, List<Track>? queue = null, int queueIndex = -1)
    {
        _currentTrack = track;
        _playerQueue = queue ?? [track];
        _playerQueueIndex = queueIndex >= 0 ? queueIndex : 0;

        UpdatePlayerInfo(track.DisplayTitle, track.DisplayArtist, track.DisplayBpm, track.DisplayKey);
        PlayerDuration.Text = track.DisplayDuration;
        PlayerSeek.Value = 0;

        try
        {
            var uri = new Uri(track.Path);
            var source = MediaSource.CreateFromUri(uri);
            _player.Source = source;
            _player.Play();
        }
        catch (Exception ex)
        {
            _ = ShowPlayerErrorAsync(ex.Message);
        }
    }

    // ── Event handlers playera ───────────────────────────────────────────────

    private void BtnPlayPause_Click(object sender, RoutedEventArgs e)
    {
        if (_player.Source is null)
        {
            // Spróbuj zagrać pierwszy track z biblioteki
            if (ContentFrame.Content is LibraryPage lib)
                lib.PlayFirstTrack();
            return;
        }

        if (_player.PlaybackSession.PlaybackState == MediaPlaybackState.Playing)
            _player.Pause();
        else
            _player.Play();
    }

    private void BtnPrev_Click(object sender, RoutedEventArgs e)
    {
        if (_playerQueue.Count == 0) return;
        _playerQueueIndex = Math.Max(0, _playerQueueIndex - 1);
        PlayTrack(_playerQueue[_playerQueueIndex], _playerQueue, _playerQueueIndex);
    }

    private void BtnNext_Click(object sender, RoutedEventArgs e)
    {
        if (_playerQueue.Count == 0) return;
        _playerQueueIndex = Math.Min(_playerQueue.Count - 1, _playerQueueIndex + 1);
        PlayTrack(_playerQueue[_playerQueueIndex], _playerQueue, _playerQueueIndex);
    }

    private void PlaybackSession_StateChanged(MediaPlaybackSession session, object args)
    {
        DispatcherQueue.TryEnqueue(() =>
        {
            BtnPlayPause.Content = session.PlaybackState == MediaPlaybackState.Playing ? "⏸" : "⏵";
        });
    }

    private void PlaybackSession_DurationChanged(MediaPlaybackSession session, object args)
    {
        DispatcherQueue.TryEnqueue(() =>
        {
            var dur = session.NaturalDuration;
            PlayerDuration.Text = FormatTime(dur);
        });
    }

    private void Player_MediaEnded(MediaPlayer sender, object args)
    {
        DispatcherQueue.TryEnqueue(() =>
        {
            // Autoplay: następny w kolejce
            if (_playerQueueIndex < _playerQueue.Count - 1)
                BtnNext_Click(this, null!);
        });
    }

    private void PositionTimer_Tick(object? sender, object e)
    {
        if (_isSeeking) return;
        var session = _player.PlaybackSession;
        if (session.PlaybackState == MediaPlaybackState.None) return;

        var dur = session.NaturalDuration.TotalSeconds;
        var pos = session.Position.TotalSeconds;

        PlayerPosition.Text = FormatTime(session.Position);
        PlayerSeek.Value = dur > 0 ? pos / dur : 0;
    }

    // ── Seek slider ──────────────────────────────────────────────────────────

    private void PlayerSeek_ManipulationStarted(object sender, ManipulationStartedRoutedEventArgs e)
    {
        _isSeeking = true;
    }

    private void PlayerSeek_ManipulationCompleted(object sender, ManipulationCompletedRoutedEventArgs e)
    {
        _isSeeking = false;
        var dur = _player.PlaybackSession.NaturalDuration.TotalSeconds;
        if (dur > 0)
            _player.PlaybackSession.Position = TimeSpan.FromSeconds(PlayerSeek.Value * dur);
    }

    private void PlayerSeek_ValueChanged(object sender, Microsoft.UI.Xaml.Controls.Primitives.RangeBaseValueChangedEventArgs e)
    {
        if (!_isSeeking) return;
        var dur = _player.PlaybackSession.NaturalDuration.TotalSeconds;
        if (dur > 0)
            PlayerPosition.Text = FormatTime(TimeSpan.FromSeconds(e.NewValue * dur));
    }

    // ── Nawigacja ────────────────────────────────────────────────────────────

    private void Navigate(string tag)
    {
        if (_pages.TryGetValue(tag, out var pageType))
            ContentFrame.Navigate(pageType);
    }

    private void SelectNavItem(string tag)
    {
        _suppressNavigation = true;
        try
        {
            foreach (var item in NavView.MenuItems.OfType<NavigationViewItem>())
                if (item.Tag?.ToString() == tag) { NavView.SelectedItem = item; return; }
            foreach (var item in NavView.FooterMenuItems.OfType<NavigationViewItem>())
                if (item.Tag?.ToString() == tag) { NavView.SelectedItem = item; return; }
        }
        finally
        {
            _suppressNavigation = false;
        }
    }

    private void NavView_SelectionChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs e)
    {
        if (_suppressNavigation) return;
        if (e.SelectedItem is NavigationViewItem { Tag: string tag })
            Navigate(tag);
    }

    private void GlobalSearch_QuerySubmitted(AutoSuggestBox sender, AutoSuggestBoxQuerySubmittedEventArgs e)
    {
        Navigate("Library");
        SelectNavItem("Library");
        if (ContentFrame.Content is LibraryPage lib)
            lib.ApplySearch(e.QueryText);
    }

    private void BtnSettings_Click(object sender, RoutedEventArgs e)
    {
        Navigate("Settings");
        SelectNavItem("Settings");
    }

    public void NavigateTo(string tag)
    {
        Navigate(tag);
        SelectNavItem(tag);
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    private static string FormatTime(TimeSpan ts) =>
        ts.TotalHours >= 1
            ? $"{(int)ts.TotalHours}:{ts.Minutes:D2}:{ts.Seconds:D2}"
            : $"{ts.Minutes}:{ts.Seconds:D2}";

    private async Task ShowPlayerErrorAsync(string msg)
    {
        var dlg = new ContentDialog
        {
            Title = "Błąd odtwarzania",
            Content = msg,
            CloseButtonText = "OK",
            XamlRoot = Content.XamlRoot,
        };
        await dlg.ShowAsync();
    }
}
