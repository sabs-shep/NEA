using GUI_s_ForNea;
using NEAGUIs.Python;
using Python.Runtime;
using System;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Animation;

namespace NEAGUIs
{
    public partial class AIChatUI : UI
    {
        private double CurrentWidth;
        private double TargetWidth;
        private bool IsAnimating = false;
        private string conversationId;

        // ### PYTHON AI CONTROLLER INSTANCE
        private dynamic ai;

        // expose a small setter so external code can change conversation id
        public void ConversationIdSetter(string id)
        {
            try { PyControllers.PyBridge.Call(ai, "set_conversation_id", id); }
            catch { }
        }

        // ### MODES
        private bool SearchMode = false;
        private bool ThinkMode = false;

        // ### INITIALISATION
        public AIChatUI()
        {
            conversationId = GenerateDefaultConversationId();
            InitializeComponent();
            CurrentWidth = LeftColumn.Width.Value;

            // ### HOT RELOAD FOR AIController.py
            string pythonScripts = System.IO.Path.Combine(AppContext.BaseDirectory, "PythonScripts");
            PyBridge.EnableFileWatcher("AIController", pythonScripts);

            // ### CREATE PYTHON AI CONTROLLER INSTANCE
            ai = PyControllers.Instance.TryGet("AI")
                 ?? PyControllers.GetOrCreate(
                        key: "AI",
                        moduleName: "AIController",
                        className: "AIController",
                        args: new object[] { "AI", "default" }
                    );
            // Diagnostic: log Python ai identity
            LogAiIdentity("after GetOrCreate");
            PyControllers.PyBridge.Call(ai, "set_conversation_id", conversationId);

            // ### LOAD HISTORY INTO UI
            LoadConversationHistory();
            LoadConversationList();
        }

        // ### Diagnostic helper
        private void LogAiIdentity(string when)
        {
            try
            {
                // attempt to get a Python-side id or repr if available
                string repr = ai is null ? "<null>" : ai.__repr__?.ToString() ?? "<no-repr>";
                System.Diagnostics.Debug.WriteLine($"AI instance {when}: {repr}");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"AI identity log failed ({when}): {ex.Message}");
            }
        }

        private void ChangeConversation_Click(object sender, RoutedEventArgs e)
        {
            string newId = ConversationIdBox.Text.Trim();

            newId = string.Concat(newId.Split(System.IO.Path.GetInvalidFileNameChars()));

            if (string.IsNullOrWhiteSpace(newId))
            {
                MessageBox.Show("Conversation ID cannot be empty.");
                return;
            }

            conversationId = newId;

            PyControllers.PyBridge.Call(ai, "set_conversation_id", newId);
            LogAiIdentity("after set_conversation_id (ChangeConversation)");

            ConversationPanel.Children.Clear();
            LoadConversationHistory();

            MessageBox.Show($"Switched to conversation: {newId}");
        }

        private void LoadConversationList()
        {
            ConversationList.Children.Clear();

            string folder = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "NEAApp",
                "SaveData",
                "conversations"
            );

            if (!Directory.Exists(folder))
                return;

            foreach (var file in Directory.GetFiles(folder, "*.json"))
            {
                string name = Path.GetFileNameWithoutExtension(file);

                var btn = new Button
                {
                    Content = name,
                    Margin = new Thickness(0, 0, 0, 5),
                    Background = (Brush)FindResource("PrimaryColor"),
                    Foreground = Brushes.Black,
                    Tag = name
                };

                btn.Click += ConversationButton_Click;

                ConversationList.Children.Add(btn);
            }
        }

        private void ConversationButton_Click(object sender, RoutedEventArgs e)
        {
            string id = (string)((Button)sender).Tag;

            ConversationIdBox.Text = id;

            PyControllers.PyBridge.Call(ai, "set_conversation_id", id);
            LogAiIdentity("after set_conversation_id (ConversationButton)");

            ConversationPanel.Children.Clear();
            LoadConversationHistory();
        }

        private string GenerateDefaultConversationId()
        {
            return "Conversation_" + DateTime.Now.Ticks;
        }

        // ### LOAD HISTORY
        private void LoadConversationHistory()
        {
            try
            {
                LogAiIdentity("before get_history");
                var history = PyBridge.Call(ai, "get_history");

                foreach (var msg in history)
                {
                    string role = msg["role"].ToString();
                    string content = msg["content"].ToString();

                    if (role == "user")
                        AddUserMessage(content);
                    else
                        AddAiMessage(content);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Failed to load history: " + ex.Message);
            }
        }

        // ### LEFT PANEL COLLAPSE
        private void CollapseButton_Click(object sender, RoutedEventArgs e)
        {
            bool IsExpanded = LeftColumn.Width.Value > 100;

            TargetWidth = IsExpanded ? 40 : 200;

            DoubleAnimation Anim = new DoubleAnimation
            {
                From = CurrentWidth,
                To = TargetWidth,
                Duration = TimeSpan.FromMilliseconds(250),
                AccelerationRatio = 0.2,
                DecelerationRatio = 0.2
            };

            Anim.Completed += (s, a) =>
            {
                IsAnimating = false;
                CurrentWidth = TargetWidth;
                LeftColumn.Width = new GridLength(TargetWidth);
                CompositionTarget.Rendering -= AnimateWidth;
            };

            CurrentWidth = LeftColumn.Width.Value;
            IsAnimating = true;

            CompositionTarget.Rendering += AnimateWidth;
            this.BeginAnimation(DummyProperty, Anim);

            double Angle = IsExpanded ? 90 : 0;
            CollapseButtonRotate.BeginAnimation(
                RotateTransform.AngleProperty,
                new DoubleAnimation(Angle, TimeSpan.FromMilliseconds(250))
            );

            DoubleAnimation FadeAnim = (DoubleAnimation)FindResource(
                IsExpanded ? "FadeOutAnimation" : "FadeInAnimation"
            );
            LeftPanel.BeginAnimation(OpacityProperty, FadeAnim);
        }

        // ### WIDTH ANIMATION LOOP
        private void AnimateWidth(object sender, EventArgs e)
        {
            if (!IsAnimating) return;

            double Value = (double)GetValue(DummyProperty);
            LeftColumn.Width = new GridLength(Value);
        }

        // ### DUMMY PROPERTY
        public static readonly DependencyProperty DummyProperty =
            DependencyProperty.Register("Dummy", typeof(double), typeof(AIChatUI));

        // ### SCROLL TO BOTTOM
        private void ScrollToBottom()
        {
            if (ConversationScrollViewer == null) return;

            double From = ConversationScrollViewer.VerticalOffset;
            double To = ConversationScrollViewer.ScrollableHeight;

            DoubleAnimation Anim = new DoubleAnimation
            {
                From = From,
                To = To,
                Duration = TimeSpan.FromMilliseconds(250),
                AccelerationRatio = 0.2,
                DecelerationRatio = 0.2
            };

            ConversationScrollViewer.BeginAnimation(
                ScrollViewerBehavior.VerticalOffsetProperty,
                Anim
            );
        }

        // ### ADD USER MESSAGE
        private void AddUserMessage(string text)
        {
            TextBlock bubble = new TextBlock
            {
                Text = text,
                Background = Brushes.White,
                Foreground = Brushes.Black,
                Padding = new Thickness(10),
                Margin = new Thickness(0, 5, 50, 5),
                TextWrapping = TextWrapping.Wrap,
                HorizontalAlignment = HorizontalAlignment.Left,
                MaxWidth = 500
            };

            ConversationPanel.Children.Add(bubble);
            ScrollToBottom();
        }

        // ### ADD AI MESSAGE
        private void AddAiMessage(string text)
        {
            TextBlock bubble = new TextBlock
            {
                Text = text,
                Background = Brushes.LightGray,
                Foreground = Brushes.Black,
                Padding = new Thickness(10),
                Margin = new Thickness(50, 5, 0, 5),
                TextWrapping = TextWrapping.Wrap,
                HorizontalAlignment = HorizontalAlignment.Right,
                MaxWidth = 500
            };

            ConversationPanel.Children.Add(bubble);
            ScrollToBottom();
        }

        // ### SELECT CONTEXT (FIXED)
        private void SelectContext_Click(object sender, RoutedEventArgs e)
        {
            var kb = new KnowledgeBaseUI(true);

            // KB sends formatted text
            kb.OnContextSelected += (formattedText) =>
            {
                // Use the EXISTING ai instance
                LogAiIdentity("before load_kb_context");
                PyBridge.Call(ai, "load_kb_context", formattedText);
                LogAiIdentity("after load_kb_context");

                MessageBox.Show("Knowledge context added to conversation.");
            };

            NavigateTo(kb);
        }

        // ### MESSAGE INPUT — SEND TO PYTHON AI
        private void InputBox_KeyDown(object sender, System.Windows.Input.KeyEventArgs e)
        {
            if (e.Key == System.Windows.Input.Key.Enter)
            {
                string text = InputBox.Text.Trim();
                if (text.Length == 0)
                    return;

                AddUserMessage(text);

                string reply = PyBridge.Call(
                    ai,
                    "send_message",
                    text,
                    ThinkMode,
                    SearchMode
                );

                LogAiIdentity("after send_message");

                AddAiMessage(reply);

                InputBox.Clear();
                e.Handled = true;
            }
        }

        // ### STT BUTTON
        private void Stt_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("STT not implemented yet.");
        }

        // ### SEARCH MODE TOGGLE
        private void Search_Click(object sender, RoutedEventArgs e)
        {
            SearchMode = !SearchMode;
            MessageBox.Show("Search mode: " + (SearchMode ? "ON" : "OFF"));
        }

        // ### THINK MODE TOGGLE
        private void AddFile_Click(object sender, RoutedEventArgs e)
        {
            ThinkMode = !ThinkMode;
            MessageBox.Show("Think mode: " + (ThinkMode ? "ON" : "OFF"));
        }
    }

    // ### SCROLLVIEWER BEHAVIOUR
    public static class ScrollViewerBehavior
    {
        public static readonly DependencyProperty VerticalOffsetProperty =
            DependencyProperty.RegisterAttached(
                "VerticalOffset",
                typeof(double),
                typeof(ScrollViewerBehavior),
                new PropertyMetadata(0.0, OnVerticalOffsetChanged));

        public static void SetVerticalOffset(DependencyObject d, double value)
        {
            d.SetValue(VerticalOffsetProperty, value);
        }

        public static double GetVerticalOffset(DependencyObject d)
        {
            return (double)d.GetValue(VerticalOffsetProperty);
        }

        private static void OnVerticalOffsetChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
        {
            if (d is ScrollViewer viewer)
            {
                viewer.ScrollToVerticalOffset((double)e.NewValue);
            }
        }
    }
}