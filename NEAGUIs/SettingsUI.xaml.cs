// ### settings ui
using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace NEAGUIs
{
    public partial class SettingsUI : UI
    {
        private dynamic settingsController;

        // ### initialisation
        public SettingsUI()
        {
            InitializeComponent();

            // ## get python controller
            settingsController = PyControllers.GetOrCreate(
                "settings",
                "SettingsController",
                "SettingsController",
                "settings"
            );

            LoadCategories();
        }

        // ### load categories
        private void LoadCategories()
        {
            CategoryList.Items.Clear();

            dynamic categories = settingsController.list_categories();

            foreach (var cat in categories)
                CategoryList.Items.Add(cat.ToString());

            if (CategoryList.Items.Count > 0)
                CategoryList.SelectedIndex = 0;
        }

        // ### category changed
        private void CategoryList_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (CategoryList.SelectedItem == null)
                return;

            LoadSettings(CategoryList.SelectedItem.ToString());
        }

        // ### load settings for category
        private void LoadSettings(string category)
        {
            SettingsPanel.Children.Clear();

            dynamic settings = settingsController.get_settings_for_category(category);

            foreach (var pair in settings.items())
            {
                string key = pair[0].ToString();
                dynamic pref = pair[1];

                string description = pref["description"].ToString();
                string current = pref["current"]?.ToString();
                var options = pref["options"];

                // ### description label
                SettingsPanel.Children.Add(new TextBlock
                {
                    Text = description,
                    FontWeight = FontWeights.Bold,
                    Margin = new Thickness(0, 15, 0, 5),
                    FontSize = 16,
                    Foreground = Brushes.Black
                });

                // ### dropdown
                if (options != null && options.__len__() > 0)
                {
                    ComboBox combo = new ComboBox
                    {
                        Width = 250,
                        Margin = new Thickness(0, 0, 0, 10),
                        Background = (Brush)Resources["PrimaryColor"],
                        Foreground = Brushes.Black,
                        BorderBrush = Brushes.Transparent,
                        BorderThickness = new Thickness(0)
                    };

                    foreach (var opt in options)
                        combo.Items.Add(opt.ToString());

                    combo.SelectedItem = current;
                    combo.SelectionChanged += (s, e) =>
                    {
                        settingsController.set_current(key, combo.SelectedItem.ToString());

                        if (key == "themes")
                            ApplyTheme(combo.SelectedItem.ToString() + ".xaml");
                    };

                    SettingsPanel.Children.Add(combo);
                }
                else
                {
                    // ### detect numeric
                    bool isNumeric = int.TryParse(current, out _);

                    if (isNumeric)
                    {
                        // ### numeric textbox
                        TextBox numBox = new TextBox
                        {
                            Text = current,
                            Width = 250,
                            Margin = new Thickness(0, 0, 0, 10),
                            Background = (Brush)Resources["PrimaryColor"],
                            Foreground = Brushes.Black,
                            BorderBrush = Brushes.Transparent,
                            BorderThickness = new Thickness(0)
                        };

                        numBox.TextChanged += (s, e) =>
                        {
                            if (int.TryParse(numBox.Text, out int value))
                                settingsController.set_current(key, value);
                        };

                        SettingsPanel.Children.Add(numBox);
                    }
                    else
                    {
                        // ### normal textbox
                        TextBox box = new TextBox
                        {
                            Text = current,
                            Width = 250,
                            Margin = new Thickness(0, 0, 0, 10),
                            Background = (Brush)Resources["PrimaryColor"],
                            Foreground = Brushes.Black,
                            BorderBrush = Brushes.Transparent,
                            BorderThickness = new Thickness(0)
                        };

                        box.TextChanged += (s, e) =>
                        {
                            settingsController.set_current(key, box.Text);
                        };

                        SettingsPanel.Children.Add(box);
                    }
                }
            }
        }
    }
}