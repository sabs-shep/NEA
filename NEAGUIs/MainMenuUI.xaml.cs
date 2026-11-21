using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;

namespace NEAGUIs
{
    public partial class MainMenuUI : UI
    {
        private readonly List<string> menuItems = new()
        {
            "AI Chat",
            "To‑Do List",
            "Knowledge Base",
            "Colour Tester",
            "Settings"
        };

        public MainMenuUI()
        {
            InitializeComponent();
            BuildMenu();
        }

        private void BuildMenu()
        {
            foreach (var label in menuItems)
            {
                var btn = new Button
                {
                    Content = label,
                    Height = 50,
                    Margin = new Thickness(0, 0, 0, 10),
                    Background = AccentBrush, // uses UI base property
                    Foreground = System.Windows.Media.Brushes.Black,
                    FontWeight = FontWeights.Bold,
                    Tag = label
                };

                btn.Click += MenuButton_Click;
                MenuList.Children.Add(btn);
            }
        }

        private void MenuButton_Click(object sender, RoutedEventArgs e)
        {
            if (sender is not Button btn || btn.Tag is not string label)
                return;

            switch (label)
            {
                case "AI Chat":
                    // Use the singleton AIChatUI instance to avoid re-creation
                    var chat = GUI_s_ForNea.App.GetOrCreateChatInstance();
                    NavigateTo(chat);
                    break;

                case "To‑Do List":
                    NavigateTo<ToDoListUI>();
                    break;

                case "Knowledge Base":
                    NavigateTo<KnowledgeBaseUI>();
                    break;

                case "Colour Tester":
                    NavigateTo<ColourTestUI>();
                    break;

                case "Settings":
                    NavigateTo<SettingsUI>();
                    break;
            }
        }
    }
}