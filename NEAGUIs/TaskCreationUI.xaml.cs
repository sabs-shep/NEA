using NEAGUIs.Python;
using Python.Runtime;
using System;
using System.Linq;
using System.Windows;
using System.Windows.Controls;

namespace NEAGUIs
{
    public partial class TaskCreationUI : UI
    {
        // ### PYTHON CONTROLLERS
        // main ToDo controller and optional task being edited
        private dynamic controller;
        private dynamic editingTask = null;

        // ### CONSTRUCTORS

        // ## TaskCreationUI (create mode)
        public TaskCreationUI()
        {
            InitializeComponent();
            InitController();
            DeleteButton.Visibility = Visibility.Hidden;
        }

        // ## TaskCreationUI (edit mode)
        public TaskCreationUI(dynamic taskToEdit)
        {
            InitializeComponent();
            InitController();

            DeleteButton.Visibility = Visibility.Visible;
            editingTask = taskToEdit;

            // # prefill basic fields
            TitleBox.Text = taskToEdit.title?.ToString() ?? "";
            DescriptionBox.Text = taskToEdit.description?.ToString() ?? "";

            if (taskToEdit.due_date != null)
                DueDatePicker.SelectedDate = DateTime.Parse(taskToEdit.due_date.ToString());

            CompleteBox.IsChecked = taskToEdit.complete;

            // # prefill tags
            try
            {
                var pyList = (PyObject)taskToEdit.tags;
                string[] tagArray = pyList.As<string[]>();
                TagsBox.Text = string.Join(", ", tagArray);
            }
            catch { TagsBox.Text = ""; }

            // # prefill priority
            try
            {
                string pyPriority = taskToEdit.priority.ToString();
                if (!string.IsNullOrEmpty(pyPriority))
                    pyPriority = pyPriority.ToUpper();

                foreach (ComboBoxItem item in PriorityBox.Items)
                {
                    if (item.Tag?.ToString() == pyPriority)
                    {
                        PriorityBox.SelectedItem = item;
                        break;
                    }
                }
            }
            catch { }

            // # prefill recurrence
            try
            {
                RecurrenceIntervalBox.Text = taskToEdit.reccurance[1].ToString();

                string freq = taskToEdit.reccurance[0].ToString();
                if (!string.IsNullOrEmpty(freq))
                    freq = freq.ToUpper();

                foreach (ComboBoxItem item in RecurrenceBox.Items)
                {
                    if (item.Tag?.ToString() == freq)
                    {
                        RecurrenceBox.SelectedItem = item;
                        break;
                    }
                }
            }
            catch { }
        }

        // ### CONTROLLER INITIALISATION

        // ## InitController
        // retrieves the ToDoListController instance from Python
        private void InitController()
        {
            controller = PyControllers.GetOrCreate(
                key: "ToDo",
                moduleName: "ToDoListController",
                className: "ToDoListController",
                args: "ToDo"
            );
        }

        // ### NAVIGATION

        // ## CancelButton_Click
        // returns to the main ToDo list
        private void CancelButton_Click(object sender, RoutedEventArgs e)
        {
            NavigateTo<ToDoListUI>();
        }

        // ## DeleteButton_Click
        // deletes the task and removes it from the KB
        private void DeleteButton_Click(object sender, RoutedEventArgs e)
        {
            if (editingTask == null)
                return;

            using (Py.GIL())
            {
                // # get KB instance
                var kb = PyControllers.GetOrCreate(
                    key: "KB",
                    moduleName: "KnowledgeBaseController",
                    className: "KnowledgeBaseController"
                );

                // # delete task and unregister from KB
                controller.delete_task(editingTask.id, kb);
            }

            NavigateTo<ToDoListUI>();
        }

        // ### SUBMIT HANDLER

        // ## SubmitButton_Click
        // creates or edits a task, and updates the KB when needed
        private void SubmitButton_Click(object sender, RoutedEventArgs e)
        {
            using (Py.GIL())
            {
                // # read basic fields
                string title = TitleBox.Text.Trim();
                string desc = DescriptionBox.Text.Trim();

                string priority = ((ComboBoxItem)PriorityBox.SelectedItem).Tag.ToString();
                string recurrence = ((ComboBoxItem)RecurrenceBox.SelectedItem).Tag.ToString();

                int interval = int.TryParse(RecurrenceIntervalBox.Text, out int i) ? i : 1;
                bool complete = CompleteBox.IsChecked == true;

                DateTime? due = DueDatePicker.SelectedDate;

                string[] tags = TagsBox.Text
                    .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

                if (editingTask == null)
                {
                    // # get KB instance
                    var kb = PyControllers.GetOrCreate(
                        key: "KB",
                        moduleName: "KnowledgeBaseController",
                        className: "KnowledgeBaseController"
                    );

                    // # create task and register in KB
                    controller.add_task(
                        title,
                        desc,
                        priority,
                        due?.ToString("yyyy-MM-dd"),
                        recurrence,
                        interval,
                        tags,
                        complete,
                        kb
                    );
                }
                else
                {
                    // # build update dictionary
                    using (PyDict updates = new PyDict())
                    {
                        updates.SetItem("title", title.ToPython());
                        updates.SetItem("description", desc.ToPython());
                        updates.SetItem("priority", priority.ToPython());
                        updates.SetItem("due_date", (due?.ToString("yyyy-MM-dd")).ToPython());

                        using (var recList = new PyList(new PyObject[]
                        {
                            recurrence.ToPython(),
                            interval.ToPython()
                        }))
                        {
                            updates.SetItem("reccurance", recList);
                        }

                        updates.SetItem("tags", tags.ToPython());
                        updates.SetItem("complete", complete.ToPython());

                        controller.edit_task(editingTask.id, updates);
                    }
                }
            }

            NavigateTo<ToDoListUI>();
        }
    }
}