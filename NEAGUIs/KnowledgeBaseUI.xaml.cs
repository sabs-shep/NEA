using GUI_s_ForNea;
using NEAGUIs.Python;
using Python.Runtime;
using System;
using System.Collections.Generic;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace NEAGUIs
{
    public partial class KnowledgeBaseUI : UI
    {
        // ### PYTHON CONTROLLER REFERENCE
        private dynamic _kb;

        // ### ALWAYS USE THE SINGLETON AIChatUI
        private readonly AIChatUI _parent;

        // ### SELECT MODE FLAG
        private readonly bool _selectMode;

        // ### CALLBACK
        public event Action<string> OnContextSelected;

        // ### DEFAULT CONSTRUCTOR (BROWSE MODE)
        public KnowledgeBaseUI()
        {
            InitializeComponent();

            _parent = App.GetOrCreateChatInstance();   // ALWAYS singleton
            _selectMode = false;

            InitialisePython();
            InitialiseTypes();
            LoadAllEntries();

            AddToContextButton.Visibility = Visibility.Collapsed;
        }

        // ### SELECT MODE CONSTRUCTOR
        public KnowledgeBaseUI(bool selectMode)
        {
            InitializeComponent();

            _parent = App.GetOrCreateChatInstance();   // ALWAYS singleton
            _selectMode = selectMode;

            InitialisePython();
            InitialiseTypes();
            LoadAllEntries();

            AddToContextButton.Visibility =
                _selectMode ? Visibility.Visible : Visibility.Collapsed;
        }

        // ### PYTHON INITIALISATION
        private void InitialisePython()
        {
            _kb = PyControllers.GetOrCreate(
                key: "KB",
                moduleName: "KnowledgeBaseController",
                className: "KnowledgeBaseController"
            );

            var tasks = PyControllers.GetOrCreate(
                key: "ToDo",
                moduleName: "ToDoListController",
                className: "ToDoListController",
                args: "ToDo"
            );

            _kb.register_type("Task", tasks);
        }

        // ### TYPE LIST INITIALISATION
        private void InitialiseTypes()
        {
            TypeList.Items.Add("All");
            TypeList.Items.Add("Task");
            TypeList.SelectedIndex = 0;
        }

        // ### PYTHON DICT HELPERS
        private bool PyHasKey(dynamic pyDict, string key)
        {
            if (pyDict == null || key == null)
                return false;

            using (Py.GIL())
            {
                using var d = new PyDict(pyDict);
                return d.HasKey(new PyString(key));
            }
        }

        // ### LOAD ALL KNOWLEDGE ENTRIES
        private void LoadAllEntries()
        {
            EntryList.Items.Clear();

            dynamic entries = _kb.get_all_entries();
            foreach (var e in entries)
            {
                string type = e.get_type();
                string refId = e.get_id();

                dynamic info = _kb.get_information(refId);

                string title = PyHasKey(info, "title") ? (string)info["title"] : null;
                string description = PyHasKey(info, "description") ? (string)info["description"] : null;

                string label =
                    title ??
                    description ??
                    $"{type} ({refId})";

                EntryList.Items.Add(new EntryItem
                {
                    Type = type,
                    RefId = refId,
                    Title = title,
                    Description = description,
                    Metadata = PyHasKey(info, "metadata") ? info["metadata"] : null,
                    Label = label
                });
            }
        }

        // ### SEARCH HANDLING
        private void SearchButton_Click(object sender, RoutedEventArgs e)
        {
            RunSearch();
        }

        private void SearchBox_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter)
                RunSearch();
        }

        private void RunSearch()
        {
            string query = SearchBox.Text ?? string.Empty;

            EntryList.Items.Clear();

            dynamic results = _kb.search(query);
            foreach (var r in results)
            {
                string type = r.type;
                string refId = r.ref_id;

                dynamic info = _kb.get_information(refId);

                string title = PyHasKey(info, "title") ? (string)info["title"] : null;
                string description = PyHasKey(info, "description") ? (string)info["description"] : null;

                string label =
                    title ??
                    description ??
                    r.label ??
                    $"{type} ({refId})";

                EntryList.Items.Add(new EntryItem
                {
                    Type = type,
                    RefId = refId,
                    Title = title,
                    Description = description,
                    Metadata = PyHasKey(info, "metadata") ? info["metadata"] : null,
                    Label = label
                });
            }
        }

        // ### TYPE FILTERING
        private void TypeList_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (TypeList.SelectedItem == null)
                return;

            string selectedType = TypeList.SelectedItem.ToString();

            EntryList.Items.Clear();

            if (selectedType == "All")
            {
                LoadAllEntries();
                return;
            }

            dynamic entries = _kb.filter_by_type(selectedType);
            foreach (var e2 in entries)
            {
                string type = e2.get_type();
                string refId = e2.get_id();

                dynamic info = _kb.get_information(refId);

                string title = PyHasKey(info, "title") ? (string)info["title"] : null;
                string description = PyHasKey(info, "description") ? (string)info["description"] : null;

                string label =
                    title ??
                    description ??
                    $"{type} ({refId})";

                EntryList.Items.Add(new EntryItem
                {
                    Type = type,
                    RefId = refId,
                    Title = title,
                    Description = description,
                    Metadata = PyHasKey(info, "metadata") ? info["metadata"] : null,
                    Label = label
                });
            }
        }

        // ### DETAIL PANEL
        private void EntryList_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (EntryList.SelectedItem is not EntryItem item)
                return;

            dynamic info = _kb.get_information(item.RefId);
            DetailBox.Text = FormatDictionary(info);
        }

        private string FormatDictionary(dynamic info)
        {
            if (info == null)
                return "No information.";

            var sb = new StringBuilder();

            foreach (var kv in info.items())
            {
                string key = kv[0];
                object value = kv[1];

                sb.AppendLine($"{key}: {value}");
            }

            return sb.ToString();
        }

        // ### ADD TO CONTEXT
        private void AddToContext_Click(object sender, RoutedEventArgs e)
        {
            if (!_selectMode)
                return;

            if (EntryList.SelectedItem is not EntryItem item)
                return;

            dynamic info = _kb.get_information(item.RefId);

            string formatted = FormatDictionary(info);

            OnContextSelected?.Invoke(formatted);

            // ALWAYS navigate back to the singleton AIChatUI
            NavigateTo(App.GetOrCreateChatInstance());
        }

        // ### ENTRY ITEM CLASS
        private class EntryItem
        {
            public string Type { get; set; }
            public string RefId { get; set; }
            public string Title { get; set; }
            public string Description { get; set; }
            public dynamic Metadata { get; set; }
            public string Label { get; set; }

            public override string ToString() => Label;
        }
    }
}