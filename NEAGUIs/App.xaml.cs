using NEAGUIs;
using Python.Runtime;
using System;
using System.IO;
using System.Linq;
using System.Windows;

namespace GUI_s_ForNea
{
    public partial class App : Application
    {
        // Singleton holder for AIChatUI to prevent multiple constructions
        private static AIChatUI? _chatInstance;

        public static AIChatUI GetOrCreateChatInstance()
        {
            if (_chatInstance == null)
            {
                _chatInstance = new AIChatUI();
                // ensure it's not garbage-collectable by leaving it referenced
            }

            return _chatInstance;
        }

        // Allow AIChatUI to set conversation id via this helper to avoid
        // invoking constructors with args.
        public static void SetChatConversationId(string id)
        {
            try
            {
                GetOrCreateChatInstance().ConversationIdSetter(id);
            }
            catch { }
        }

        // ### STARTUP OVERRIDE
        protected override void OnStartup(StartupEventArgs e)
        {
            // # Start from the .exe location
            string baseDir = AppContext.BaseDirectory;

            // # Find the NEA root folder
            string neaRoot = FindAncestorNamed(baseDir, "NEA");
            if (neaRoot == null)
            {
                MessageBox.Show("Could not locate the NEA folder. Ensure the app is inside the NEA directory structure.");
                Shutdown();
                return;
            }

            // ### BUILD PATHS
            string programRoot = Path.Combine(neaRoot, "Program");
            string pythonRoot = Path.Combine(programRoot, "python");
            string pythonScripts = Path.Combine(programRoot, "PythonScripts");

            // ### VALIDATE PYTHON RUNTIME
            string dllPath = Path.Combine(pythonRoot, "python313.dll");
            if (!File.Exists(dllPath))
            {
                MessageBox.Show($"python313.dll not found at: {dllPath}");
                Shutdown();
                return;
            }

            if (!Directory.Exists(Path.Combine(pythonRoot, "Lib")))
            {
                MessageBox.Show("Missing Lib/ folder in the python runtime.");
                Shutdown();
                return;
            }

            if (!Directory.Exists(pythonScripts))
            {
                MessageBox.Show("PythonScripts folder not found.");
                Shutdown();
                return;
            }

            // ### CONFIGURE PYTHON.NET
            Runtime.PythonDLL = dllPath;
            PythonEngine.PythonHome = pythonRoot;

            PythonEngine.PythonPath = string.Join(";", new[]
            {
                Path.Combine(pythonRoot, "Lib"),
                Path.Combine(pythonRoot, "DLLs"),
                Path.Combine(pythonRoot, "Lib", "site-packages"),
                pythonScripts
            });

            // ### INITIALISE PYTHON
            PythonEngine.Initialize();

            // ### ENSURE PYTHONSCRIPTS IS IN sys.path
            using (Py.GIL())
            {
                dynamic sys = Py.Import("sys");

                // # Insert PythonScripts into sys.path if missing
                if (!sys.path.__contains__(pythonScripts))
                    sys.path.insert(0, pythonScripts);
            }

            // ### DEBUG OUTPUT
            System.Diagnostics.Debug.WriteLine($"BaseDir:          {baseDir}");
            System.Diagnostics.Debug.WriteLine($"NEA Root:         {neaRoot}");
            System.Diagnostics.Debug.WriteLine($"Program Root:     {programRoot}");
            System.Diagnostics.Debug.WriteLine($"Python Root:      {pythonRoot}");
            System.Diagnostics.Debug.WriteLine($"Python DLL:       {dllPath}");
            System.Diagnostics.Debug.WriteLine($"PythonScripts:    {pythonScripts}");
            System.Diagnostics.Debug.WriteLine($"PythonEnginePath: {PythonEngine.PythonPath}");

            base.OnStartup(e);
        }
        private void Application_Startup(object sender, StartupEventArgs e)
        {
            // After Python is fully initialised, show the first UI
            var login = new LoginUI();
            login.Show();
        }

        // ### CLEAN SHUTDOWN
        protected override void OnExit(ExitEventArgs e)
        {
            base.OnExit(e);

            if (PythonEngine.IsInitialized)
                PythonEngine.Shutdown();
        }

        // ### DIRECTORY ASCENT HELPER
        private static string FindAncestorNamed(string startDir, string folderName)
        {
            var dir = new DirectoryInfo(startDir);
            while (dir != null)
            {
                if (string.Equals(dir.Name, folderName, StringComparison.OrdinalIgnoreCase))
                    return dir.FullName;

                dir = dir.Parent;
            }
            return null;
        }
    }
}