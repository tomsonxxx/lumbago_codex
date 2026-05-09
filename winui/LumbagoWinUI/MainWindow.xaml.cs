using LumbagoWinUI.Pages;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace LumbagoWinUI;

public sealed partial class MainWindow : Window
{
    private static readonly Dictionary<string, Type> _pages = new()
    {
        ["Start"]      = typeof(StartPage),
        ["Library"]    = typeof(LibraryPage),
        ["Import"]     = typeof(ImportPage),
        ["Duplicates"] = typeof(DuplicatesPage),
        ["Converter"]  = typeof(ConverterPage),
        ["Settings"]   = typeof(SettingsPage),
    };

    public MainWindow()
    {
        InitializeComponent();
        ExtendsContentIntoTitleBar = true;
        Navigate("Library");
        SelectNavItem("Library");
    }

    private void Navigate(string tag)
    {
        if (_pages.TryGetValue(tag, out var pageType))
            ContentFrame.Navigate(pageType);
    }

    private void SelectNavItem(string tag)
    {
        foreach (var item in NavView.MenuItems.OfType<NavigationViewItem>())
            if (item.Tag?.ToString() == tag) { NavView.SelectedItem = item; return; }
        foreach (var item in NavView.FooterMenuItems.OfType<NavigationViewItem>())
            if (item.Tag?.ToString() == tag) { NavView.SelectedItem = item; return; }
    }

    private void NavView_SelectionChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs e)
    {
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

    public void UpdatePlayerInfo(string title, string artist, string bpm, string key)
    {
        PlayerTitle.Text = title;
        PlayerArtist.Text = artist;
        PlayerBpm.Text = string.IsNullOrEmpty(bpm) ? "— BPM" : $"{bpm} BPM";
        PlayerKey.Text = string.IsNullOrEmpty(key) ? "—" : key;
    }
}
