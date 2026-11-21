using NEAGUIs.Python;
using Python.Runtime;
using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.IO;
using System.Windows.Input;

namespace NEAGUIs
{
    public partial class ToDoListUI : UI
    {
        // ### FIELDS
        private ObservableCollection<dynamic> tasks = new ObservableCollection<dynamic>();  // #python task objects
        private dynamic controller;                                                        // #python ToDoListController
        private dynamic ai_controller;                                                     // #python AIController (passed to search_tasks)

        // ### INITIALISATION
        public ToDoListUI()
        {
            InitializeComponent();

            // ## get Python ToDoListController
            controller = PyControllers.GetOrCreate(
                key: "ToDo",
                moduleName: "ToDoListController",
                className: "ToDoListController",
                args: "ToDo"
            );

            // ## get Python AIController (reuse existing if present, otherwise create canonical "AI")
            ai_controller = PyControllers.Instance.TryGet("AI")
                            ?? PyControllers.Instance.TryGet("AI_default")
                            ?? PyControllers.GetOrCreate(
                                key: "AI",
                                moduleName: "AIController",
                                className: "AIController",
                                args: new object[] { "AI", "default" }
                            );

            // ## load tasks immediately
            LoadAllTasks();
            ApplyFilters();

            // ## move robot on load
            Loaded += (s, e) =>
            {
                MoveRobotTo(UpcomingTab);
                LoadAllTasks();
                ApplyFilters();
            };

            // ## bind UI list
            TaskList.ItemsSource = tasks;

            // ## ENTER triggers search
            SearchBox.KeyDown += SearchBox_KeyDown;
        }

        // ### LOADERS
        private void LoadAllTasks()
        {
            tasks.Clear();

            using (Py.GIL())
            {
                dynamic pyList = controller.get_all_tasks();

                foreach (dynamic t in pyList)
                    tasks.Add(t);
            }
        }

        // ### FILTERING (PYTHON HANDLES AI + KEYWORD LEARNING)
        private void ApplyFilters()
        {
            if (controller == null)
                return;

            tasks.Clear();

            string query = SearchBox.Text.Trim().ToLower();
            string sort = (SortBox.SelectedItem as ComboBoxItem)?.Content.ToString();

            using (Py.GIL())
            {
                dynamic pyList;

                // ## NO QUERY → NORMAL FILTERING
                if (string.IsNullOrWhiteSpace(query))
                {
                    pyList = controller.get_all_tasks();
                }
                else
                {
                    // ## PYTHON handles AI + keyword learning
                    pyList = controller.search_tasks(query, ai_controller);
                }

                // ## add tasks to UI list
                foreach (dynamic t in pyList)
                    tasks.Add(t);

                // ### SORTING
                var sorted = tasks.ToList();

                if (sort == "Title")
                    sorted = sorted.OrderBy(t => t.title.ToString().ToLower()).ToList();

                else if (sort == "Priority")
                    sorted = sorted.OrderBy(t => (int)t.priority).ToList();

                else if (sort == "Due Date")
                    sorted = sorted.OrderBy(t =>
                        t.due_date == null ? DateTime.MaxValue : DateTime.Parse(t.due_date.ToString())
                    ).ToList();

                else if (sort == "Created")
                    sorted = sorted.OrderBy(t =>
                        t.created_at == null ? DateTime.MinValue : DateTime.Parse(t.created_at.ToString())
                    ).ToList();

                // ## push sorted results back into ObservableCollection
                tasks.Clear();
                foreach (var t in sorted)
                    tasks.Add(t);
            }
        }

        // ### SEARCH HANDLER (ENTER TO SEARCH)
        private void SearchBox_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter)
            {
                ApplyFilters();  // #run search immediately
                e.Handled = true;// #prevent ding sound
            }
        }

        // ### SORT HANDLER
        private void SortBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            ApplyFilters();
        }

        // ### UI HELPERS
        private void MoveRobotTo(Button targetButton)
        {
            const double horizontalOffset = -50;
            const double verticalOffset = 20;

            if (targetButton == null)
                return;

            var canvas = RobotImage.Parent as Canvas;
            if (canvas == null)
                return;

            var point = targetButton.TranslatePoint(new Point(0, 0), canvas);

            double robotWidth = (RobotImage.Width > 0 ? RobotImage.Width : RobotImage.ActualWidth);
            double targetLeft = point.X + targetButton.ActualWidth / 2 - robotWidth / 2 + horizontalOffset;
            double targetTop = point.Y + verticalOffset;

            Canvas.SetLeft(RobotImage, targetLeft);
            Canvas.SetTop(RobotImage, targetTop);
        }

        private void SetAddButtonVisible(bool visible)
        {
            AddTaskButton.Visibility = visible ? Visibility.Visible : Visibility.Collapsed;
        }

        // ### TAB HANDLERS
        private void UpcomingTab_Click(object sender, RoutedEventArgs e)
        {
            MoveRobotTo(UpcomingTab);
            SetAddButtonVisible(true);
            ApplyFilters();
        }

        private void PastDueTab_Click(object sender, RoutedEventArgs e)
        {
            MoveRobotTo(PastDueTab);
            SetAddButtonVisible(false);
            tasks.Clear();

            using (Py.GIL())
            {
                dynamic pyList = controller.get_all_tasks();

                foreach (dynamic t in pyList)
                {
                    bool complete = t.complete;
                    DateTime? due = t.due_date == null
                        ? null
                        : DateTime.Parse(t.due_date.ToString());

                    if (!complete && due != null && due < DateTime.Today)
                        tasks.Add(t);
                }
            }
        }

        private void DoneTab_Click(object sender, RoutedEventArgs e)
        {
            MoveRobotTo(DoneTab);
            SetAddButtonVisible(false);
            tasks.Clear();

            using (Py.GIL())
            {
                dynamic pyList = controller.get_all_tasks();

                foreach (dynamic t in pyList)
                    if (t.complete)
                        tasks.Add(t);
            }
        }

        // ### ADD TASK
        private void AddTaskButton_Click(object sender, RoutedEventArgs e)
        {
            NavigateTo<TaskCreationUI>();
        }

        // ### ITEM CLICK
        private void Task_Click(object sender, RoutedEventArgs e)
        {
            var button = sender as Button;
            dynamic t = button?.DataContext;

            if (t != null)
                NavigateTo<TaskCreationUI>(t);
        }
    }
}