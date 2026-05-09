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
        // Window jest poza drzewem UIElement w WinUI 3 — używamy statycznej referencji.
        if (sender is Microsoft.UI.Xaml.FrameworkElement { Tag: string tag })
            App.Window?.NavigateTo(tag);
    }
}
