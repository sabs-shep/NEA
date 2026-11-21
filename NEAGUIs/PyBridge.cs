// Top-level PyBridge facade that forwards to PyControllers.PyBridge
namespace NEAGUIs
{
    public static class PyBridge
    {
        private static NEAGUIs.Python.PythonBridge Bridge => PyControllers.PyBridge;

        public static void EnableFileWatcher(string moduleName, string pythonScriptsPath)
            => Bridge.EnableFileWatcher(moduleName, pythonScriptsPath);

        public static dynamic Call(dynamic instance, string methodName, params object[] args)
            => Bridge.Call(instance, methodName, args);

        public static void Dispose()
            => Bridge.Dispose();
    }
}
