using System;
using System.IO;

public static class DebugLog
{
    private static readonly string LogPath =
        Path.Combine("C:\\temp", "nea_debug_log.txt");

    public static void Write(string message)
    {
        try
        {
            Directory.CreateDirectory("C:\\temp");
            File.AppendAllText(LogPath,
                $"{DateTime.Now:HH:mm:ss}  {message}\n");
        }
        catch { /* ignore logging failures */ }
    }
}