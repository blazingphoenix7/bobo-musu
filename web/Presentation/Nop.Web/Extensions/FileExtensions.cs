using System.IO;

namespace Nop.Web.Extensions
{
    public static class FileExtensions
    {
        public static string GetUniqueFilePath(string filePath)
        {
            var uniqueFilePath = filePath;
            var index = 1;
            while (File.Exists(uniqueFilePath))
            {
                index++;
                uniqueFilePath = Path.Combine(Path.GetDirectoryName(filePath), $"{Path.GetFileNameWithoutExtension(filePath)}({index}){Path.GetExtension(filePath)}");
            }
            return uniqueFilePath;
        }
    }
}
