using System.Windows;
using System.Windows.Media;
using NEAGUIs.Python;
using Python.Runtime;   // Needed for PyObject

namespace NEAGUIs
{
    public partial class ColourTestUI : UI
    {
        // ### Backing fields
        private string _referenceText;
        private Brush _button1Background;
        private Brush _button2Background;
        private Brush _button3Background;

        // # Python controller instance
        private dynamic controller;

        // ### Bindable properties
        public string ReferenceText
        {
            get => _referenceText;
            set { _referenceText = value; RefreshBindings(); }
        }

        public Brush Button1Background
        {
            get => _button1Background;
            set { _button1Background = value; RefreshBindings(); }
        }

        public Brush Button2Background
        {
            get => _button2Background;
            set { _button2Background = value; RefreshBindings(); }
        }

        public Brush Button3Background
        {
            get => _button3Background;
            set { _button3Background = value; RefreshBindings(); }
        }

        // ### Constructor
        public ColourTestUI()
        {
            InitializeComponent();

            // ## Load controller (cached + OOP)
            controller = PyControllers.GetOrCreate(
                key: "CT",
                moduleName: "ColourTestController",
                className: "ColourTestController",
                args: new object[] { "CT" }
            );

            // ## Optional hot reload (PythonScripts folder)
            string pythonScripts = System.IO.Path.Combine(AppContext.BaseDirectory, "PythonScripts");
            PyBridge.EnableFileWatcher("ColourTestController", pythonScripts);

            // ## Default UI state
            ReferenceText = "Click Me!";
            SetBackgroundHex("#FFFFFF");
            Button1Background = new SolidColorBrush(Color.FromRgb(255, 0, 0));
            Button2Background = new SolidColorBrush(Color.FromRgb(0, 255, 0));
            Button3Background = new SolidColorBrush(Color.FromRgb(0, 0, 255));

            DataContext = this;
        }

        // ### Refresh WPF bindings
        private void RefreshBindings()
        {
            DataContext = null;
            DataContext = this;
        }

        // ### Update button colours
        public void SetButtonColors(Color c1, Color c2, Color c3)
        {
            Button1Background = new SolidColorBrush(c1);
            Button2Background = new SolidColorBrush(c2);
            Button3Background = new SolidColorBrush(c3);
        }

        // ### Button click handlers
        private void Button1_Click(object sender, RoutedEventArgs e) => OnButtonPress(0);
        private void Button2_Click(object sender, RoutedEventArgs e) => OnButtonPress(1);
        private void Button3_Click(object sender, RoutedEventArgs e) => OnButtonPress(2);

        // ### Python call + colour update
        private void OnButtonPress(int buttonNo)
        {
            // ### Set background to the colour of the button pressed
            Color currentButtonColor = buttonNo switch
            {
                0 => ((SolidColorBrush)Button1Background).Color,
                1 => ((SolidColorBrush)Button2Background).Color,
                2 => ((SolidColorBrush)Button3Background).Color,
                _ => Colors.White
            };

            // ### Update the Frame background (via theme resource)
            BackgroundBrush = new SolidColorBrush(currentButtonColor);
            Background = new SolidColorBrush(currentButtonColor);

            // ### Call Python
            var pyResult = PyBridge.Call(controller, "get_new_colours", buttonNo);

            // ### Convert Python list-of-lists → int[][]
            int[][] colours = ConvertToIntArray(pyResult);

            // ### Apply new colours to buttons
            SetButtonColors(
                Color.FromRgb((byte)colours[0][0], (byte)colours[0][1], (byte)colours[0][2]),
                Color.FromRgb((byte)colours[1][0], (byte)colours[1][1], (byte)colours[1][2]),
                Color.FromRgb((byte)colours[2][0], (byte)colours[2][1], (byte)colours[2][2])
            );
        }

        // ### Convert Python list-of-lists to C# int[][]
        private int[][] ConvertToIntArray(PyObject pyList)
        {
            int outerCount = (int)pyList.Length();
            int[][] result = new int[outerCount][];

            for (int i = 0; i < outerCount; i++)
            {
                using PyObject inner = pyList[i];
                int innerCount = (int)inner.Length();
                result[i] = new int[innerCount];

                for (int j = 0; j < innerCount; j++)
                    result[i][j] = (int)inner[j].As<long>();
            }

            return result;
        }

        // ### Finish button
        private void Finish_Click(object sender, RoutedEventArgs e)
        {
            // ### Tell Python to save the preferred colour set
            PyBridge.Call(controller, "save_prefered_colour");

            // ### Notify user
            MessageBox.Show("Preferred colours saved!");
        }

        // ### Back button
        private void Back_Click(object sender, RoutedEventArgs e)
        {
            var pyResult = PyBridge.Call(controller, "on_back_button");

            if (pyResult == null || pyResult.IsNone())
                return;

            // Extract colours
            var colours = ConvertToIntArray(pyResult.GetItem("colours"));

            // Extract background
            using PyObject bg = pyResult.GetItem("background");
            byte br = (byte)bg[0].As<long>();
            byte bgc = (byte)bg[1].As<long>();
            byte bb = (byte)bg[2].As<long>();
            Color backgroundColor = Color.FromRgb(br, bgc, bb);

            // Apply button colours
            SetButtonColors(
                Color.FromRgb((byte)colours[0][0], (byte)colours[0][1], (byte)colours[0][2]),
                Color.FromRgb((byte)colours[1][0], (byte)colours[1][1], (byte)colours[1][2]),
                Color.FromRgb((byte)colours[2][0], (byte)colours[2][1], (byte)colours[2][2])
            );

            // Apply background
            BackgroundBrush = new SolidColorBrush(backgroundColor);
            Background = new SolidColorBrush(backgroundColor);
            RefreshBindings();
        }
    }
}