using NEAGUIs.Python;
using Newtonsoft.Json;
using Python.Runtime;
using System;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Markup;
using System.Windows.Media;

namespace NEAGUIs
{
    public class UI : Window
    {
        // ### PROGRAM ROOT (DYNAMICALLY LOCATED NEA\Program)
        private static readonly string ProgramRoot = FindProgramRoot();
        protected string saveData;
        // ### INITIALISATION
        public UI()
        {
            try
            {

                // allow app to close when last window closes
                Application.Current.ShutdownMode = ShutdownMode.OnLastWindowClose;

                try
                {
                    // locate settings.json
                    string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
                    saveData = Path.Combine(appData, "NEAApp", "SaveData");
                    string settingsPath = Path.Combine(saveData, "settings.json");

                    if (File.Exists(settingsPath))
                    {
                        // read settings.json
                        string json = File.ReadAllText(settingsPath);
                        dynamic settings = JsonConvert.DeserializeObject(json);

                        // get theme name
                        string themeName = settings["themes"]["current"];

                        // apply theme
                        ApplyTheme(themeName);
                    }
                    else
                    {
                        // load local default.xaml
                        LoadLocalDefaultTheme();
                    }
                }
                catch
                {
                    // load local default.xaml
                    LoadLocalDefaultTheme();
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("UI constructor failed: " + ex);
                throw;
            }

        }

        // ### PROGRAM ROOT LOCATOR
        private static string FindProgramRoot()
        {
            string baseDir = AppContext.BaseDirectory;
            DirectoryInfo? dir = new DirectoryInfo(baseDir);

            while (dir != null)
            {
                if (string.Equals(dir.Name, "Program", StringComparison.OrdinalIgnoreCase) &&
                    dir.Parent != null &&
                    string.Equals(dir.Parent.Name, "NEA", StringComparison.OrdinalIgnoreCase))
                {
                    return dir.FullName;
                }

                dir = dir.Parent;
            }

            throw new DirectoryNotFoundException("Could not locate NEA\\Program directory.");
        }

        // ### THEME MANAGEMENT (LOAD FROM SAVEDATA/THEMES)
        // ## loads a theme dictionary and applies it to the window
        public void ApplyTheme(string themeName)
        {
            // normalise theme name
            if (themeName.EndsWith(".xaml", StringComparison.OrdinalIgnoreCase))
                themeName = themeName.Substring(0, themeName.Length - 5);

            // build path to theme file in AppData
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            string saveData = Path.Combine(appData, "NEAApp", "SaveData");
            string themePath = Path.Combine(saveData, "Themes", themeName + ".xaml");

            try
            {
                // load dictionary from AppData
                using (var stream = new FileStream(themePath, FileMode.Open, FileAccess.Read))
                {
                    var dict = (ResourceDictionary)XamlReader.Load(stream);

                    Resources.MergedDictionaries.Clear();
                    Resources.MergedDictionaries.Add(dict);
                }
            }
            catch
            {
                // load local default.xaml
                LoadLocalDefaultTheme();
            }
        }

        // ### LOCAL DEFAULT THEME LOADER
        // ## loads default.xaml from project directory
        private void LoadLocalDefaultTheme()
        {
            // UI.cs directory (project output)
            string exeDir = Path.GetDirectoryName(typeof(UI).Assembly.Location)
                            ?? AppContext.BaseDirectory;

            string localDefault = Path.Combine(exeDir, "default.xaml");

            using (var stream = new FileStream(localDefault, FileMode.Open, FileAccess.Read))
            {
                var dict = (ResourceDictionary)XamlReader.Load(stream);

                Resources.MergedDictionaries.Clear();
                Resources.MergedDictionaries.Add(dict);
            }
        }

        // ### GLOBAL BRUSHES
        public Brush BackgroundBrush
        {
            get => (Brush)Resources["WindowBackground"];
            set => Resources["WindowBackground"] = value;
        }

        public Brush PrimaryBrush
        {
            get => (Brush)Resources["PrimaryColor"];
            set => Resources["PrimaryColor"] = value;
        }

        public Brush AccentBrush
        {
            get => (Brush)Resources["AccentColor"];
            set => Resources["AccentColor"] = value;
        }

        // ### HEX SETTERS
        public void SetBackgroundHex(string hex)
        {
            var brush = (SolidColorBrush?)new BrushConverter().ConvertFromString(hex);
            if (brush == null) throw new ArgumentException("Invalid hex colour string.");
            BackgroundBrush = brush;
        }

        public void SetPrimaryHex(string hex)
        {
            var brush = (SolidColorBrush?)new BrushConverter().ConvertFromString(hex);
            if (brush == null) throw new ArgumentException("Invalid hex colour string.");
            PrimaryBrush = brush;
        }

        public void SetAccentHex(string hex)
        {
            var brush = (SolidColorBrush?)new BrushConverter().ConvertFromString(hex);
            if (brush == null) throw new ArgumentException("Invalid hex colour string.");
            AccentBrush = brush;
        }

        protected override void OnInitialized(EventArgs e)
        {
            base.OnInitialized(e);

            // Prevent double wrapping
            if (Content is Grid g && g.Tag as string == "Wrapped")
                return;

            // Grab original content (the Viewbox)
            var original = Content as UIElement;
            if (original == null)
                return;

            // Remove original content BEFORE reparenting
            Content = null;

            // Create wrapper grid
            var wrapper = new Grid
            {
                Tag = "Wrapped",
                ColumnDefinitions =
        {
            new ColumnDefinition { Width = new GridLength(60) }, // left bar
            new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) }
        }
            };

            // Create home button
            var homeButton = new System.Windows.Controls.Button
            {
                Content = "🏠",
                FontSize = 24,
                Margin = new Thickness(10),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Top,
                Background = (Brush)Resources["PrimaryColor"],
                BorderBrush = Brushes.Transparent,
                Cursor = Cursors.Hand
            };


            homeButton.Click += (_, __) => NavigateTo<MainMenuUI>();

            // Add home button
            Grid.SetColumn(homeButton, 0);
            wrapper.Children.Add(homeButton);

            // Add original Viewbox
            Grid.SetColumn(original, 1);
            wrapper.Children.Add(original);

            // Replace window content
            Content = wrapper;
        }



        // ### SAVE THEME (SAVE INTO SAVEDATA/THEMES)
        public void SaveTheme(string fileName, string backgroundHex, string primaryHex, string accentHex)
        {
            string themeDir = Path.Combine(ProgramRoot, "SaveData", "Petrol");
            Directory.CreateDirectory(themeDir);

            string fullPath = Path.Combine(themeDir, fileName);

            var dict = new ResourceDictionary
            {
                { "WindowBackground", new SolidColorBrush((Color)ColorConverter.ConvertFromString(backgroundHex)) },
                { "PrimaryColor",    new SolidColorBrush((Color)ColorConverter.ConvertFromString(primaryHex))    },
                { "AccentColor",     new SolidColorBrush((Color)ColorConverter.ConvertFromString(accentHex))     }
            };

            using (var writer = new StreamWriter(fullPath))
            {
                XamlWriter.Save(dict, writer);
            }
        }

        // ### CLEAN SHUTDOWN
        protected override void OnClosed(EventArgs e)
        {
            base.OnClosed(e);

            // only shut down Python when the LAST window has closed
            if (Application.Current.Windows.Count == 0)
            {
                if (PythonEngine.IsInitialized)
                    PythonEngine.Shutdown();

                PyBridge.Dispose();
            }
        }

        // ### NAVIGATION
        public void NavigateTo<T>(params object[] args) where T : UI
        {
            UI next;

            // Special-case AIChatUI: reuse a single persistent instance to avoid
            // recreating the Python controller when the window is GC'd.
            if (typeof(T) == typeof(AIChatUI))
            {
                // Obtain the singleton from the application class (creates lazily)
                var chat = GUI_s_ForNea.App.GetOrCreateChatInstance();

                // If args were provided, attempt to forward them via its public API
                // (keep behaviour unchanged for other callers)
                if (args.Length == 1 && args[0] is string convId)
                {
                    // set conversation id on the existing controller/window
                    try { chat.ConversationIdSetter(convId); } catch { }
                }

                chat.Show();
                Close();
                return;
            }

            if (args.Length == 0)
                next = (UI)Activator.CreateInstance(typeof(T));
            else
                next = (UI)Activator.CreateInstance(typeof(T), args);

            // If the current window is the persistent AIChatUI, hide it instead of
            // closing so the instance (and its Python controller) remains alive.
            next.Show();
            if (this is AIChatUI)
                this.Hide();
            else
                this.Close();
        }

        public void NavigateTo(UI instance)
        {
            instance.Show();
            this.Hide();
        }
    }

    public static class PyControllers
    {
        public static readonly PythonBridge PyBridge = new PythonBridge();
        public static readonly PythonObjectManager Instance =
            new PythonObjectManager(PyBridge);

        public static dynamic GetOrCreate(
            string key,
            string moduleName,
            string className,
            params object[] args)
        {
            return Instance.GetOrCreate(key, moduleName, className, args);
        }
    }
}