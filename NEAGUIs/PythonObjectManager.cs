// ### PYTHON OBJECT MANAGER
using System.Collections.Generic;

namespace NEAGUIs.Python
{
    public class PythonObjectManager
    {
        // # Bridge reference
        private readonly PythonBridge _bridge;

        // # Active objs (per logical key)
        private readonly Dictionary<string, dynamic> _objects = new();
        // lock for thread-safety to avoid double-construction races
        private readonly object _lock = new();

        // ## Constructor
        public PythonObjectManager(PythonBridge bridge)
        {
            _bridge = bridge;
        }

        // ## Get or create obj instance
        public dynamic GetOrCreate(string key, string moduleName, string className, params object[] args)
        {
            lock (_lock)
            {
                if (_objects.TryGetValue(key, out dynamic existing))
                    return existing;

                // Use the bridge instance to create the Python object once
                dynamic obj = _bridge.CreateObject(moduleName, className, args);
                _objects[key] = obj;
                return obj;
            }
        }

        // ## Replace obj (e.g. after reload)
        public dynamic CreateNew(string key, string moduleName, string className, params object[] args)
        {
            lock (_lock)
            {
                dynamic obj = _bridge.CreateObject(moduleName, className, args);
                _objects[key] = obj;
                return obj;
            }
        }

        // ## Try get without creating
        public dynamic? TryGet(string key)
        {
            return _objects.TryGetValue(key, out dynamic c) ? c : null;
        }
    }
}