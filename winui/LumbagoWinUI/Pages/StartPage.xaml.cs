using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;

namespace LumbagoWinUI.Pages;

public sealed partial class StartPage : Page
{
    public StartPage()
    {
        InitializeComponent();
    }

    private void Card_PointerPressed(object sender, PointerRoutedEventArgs e)
    {
        if (sender is Microsoft.UI.Xaml.FrameworkElement { Tag: string tag } &&
            App.Current is App &&
            Frame.Parent is NavigationView nav &&
            nav.Parent?.Parent is MainWindow win)
        {
            win.NavigateTo(tag);
        }
    }
}
