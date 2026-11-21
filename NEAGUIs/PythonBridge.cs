// ### PYTHON BRIDGE WITH CACHING + HOT RELOAD (NULL-SAFE)
using System;
using System.Collections.Generic;
using System.IO;
using Python.Runtime;

namespace NEAGUIs.Python
{
    public class PythonBridge : IDisposable
    {
        // ### Caches
        private readonly Dictionary<string, dynamic> moduleCache = new();
        private readonly Dictionary<string, dynamic> classCache = new();
        private readonly Dictionary<string, dynamic> instanceCache = new();

        // ### File watchers for hot reload
        private readonly Dictionary<string, FileSystemWatcher> watchers = new();

        // ## Create a Python object instance (with instance caching)
        public dynamic CreateObject(string moduleName, string className, params object[] args)
        {
            using (Py.GIL())
            {
                string key = moduleName + "." + className;

                // Diagnostic: log calls to CreateObject
                DebugLog.Write($"PythonBridge.CreateObject called: {key}, argsCount={(args?.Length ?? 0)}");

                // Return existing instance if it exists
                if (instanceCache.TryGetValue(key, out dynamic existing))
                {
                    DebugLog.Write($"PythonBridge.CreateObject: returning cached instance for {key}");
                    return existing;
                }

                // Import or get cached module
                dynamic module = GetOrImportModule(moduleName);

                // Get or cache class
                dynamic cls = GetOrCacheClass(moduleName, className, module);

                // Create instance
                dynamic instance;
                if (args is null || args.Length == 0)
                    instance = cls();
                else if (args.Length == 1)
                    instance = cls(args[0]);
                else
                    instance = cls.__call__(args);

                // Cache instance
                instanceCache[key] = instance;
                DebugLog.Write($"PythonBridge.CreateObject: created and cached instance for {key}\nStack:\n{new System.Diagnostics.StackTrace()}");
                return instance;
            }
        }

        // ## Call a method on a Python object instance
        public dynamic Call(dynamic instance, string methodName, params object[] args)
        {
            using (Py.GIL())
            {
                dynamic method = instance.GetAttr(methodName);

                if (args.Length == 0)
                    return method();

                if (args.Length == 1)
                    return method(args[0]);

                return method.__call__(args);
            }
        }

        // ## Reload a module manually (hot reload)
        public void ReloadModule(string moduleName)
        {
            using (Py.GIL())
            {
                if (!moduleCache.TryGetValue(moduleName, out dynamic module))
                    return;

                dynamic importlib = Py.Import("importlib");
                importlib.reload(module);

                // Remove cached classes from this module
                var toRemove = new List<string>();
                foreach (var key in classCache.Keys)
                    if (key.StartsWith(moduleName + ".", StringComparison.Ordinal))
                        toRemove.Add(key);

                foreach (var key in toRemove)
                    classCache.Remove(key);

                // IMPORTANT: DO NOT clear instanceCache here.
                // We keep existing instances alive to avoid reloading models.
            }
        }

        // ## Enable file watcher for automatic hot reload
        public void EnableFileWatcher(string moduleName, string pythonScriptsPath)
        {
            string filePath = Path.Combine(pythonScriptsPath, moduleName + ".py");

            if (Path.GetDirectoryName(filePath) is not string dir)
                return;

            string file = Path.GetFileName(filePath);

            if (!Directory.Exists(dir))
                return;

            var watcher = new FileSystemWatcher(dir, file)
            {
                NotifyFilter = NotifyFilters.LastWrite |
                               NotifyFilters.Size |
                               NotifyFilters.FileName
            };

            watcher.Changed += (_, __) => ReloadModule(moduleName);
            watcher.Renamed += (_, __) => ReloadModule(moduleName);

            watcher.EnableRaisingEvents = true;
            watchers[moduleName] = watcher;
        }

        // ## Internal: import or return cached module
        private dynamic GetOrImportModule(string moduleName)
        {
            if (moduleCache.TryGetValue(moduleName, out dynamic cached))
                return cached;

            dynamic module = Py.Import(moduleName);
            moduleCache[moduleName] = module;
            return module;
        }

        // ## Internal: get or cache class
        private dynamic GetOrCacheClass(string moduleName, string className, dynamic module)
        {
            string key = moduleName + "." + className;

            if (classCache.TryGetValue(key, out dynamic cached))
                return cached;

            dynamic cls = module.GetAttr(className);
            classCache[key] = cls;
            return cls;
        }

        // ## Dispose watchers
        public void Dispose()
        {
            foreach (var w in watchers.Values)
                w.Dispose();

            watchers.Clear();
        }
    }
}