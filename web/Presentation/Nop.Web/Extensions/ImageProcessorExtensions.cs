using System;
using SixLabors.ImageSharp;
using SixLabors.ImageSharp.PixelFormats;
using SixLabors.ImageSharp.Processing;
using SixLabors.ImageSharp.Processing.Filters;
using SixLabors.ImageSharp.Processing.Transforms;

namespace Nop.Web.Extensions
{
    public static class ImageProcessorExtensions
    {
        /*
        public static bool MakeThumbnail(string filePath, string thumbnailPath, int width = 128, int height = 128)
        {
            try
            {
                using (var pngStream = new FileStream(filePath, FileMode.Open, FileAccess.Read))
                using (var image = new Bitmap(pngStream))
                {
                    var resized = new Bitmap(width, height);
                    using (var graphics = Graphics.FromImage(resized))
                    {
                        graphics.CompositingQuality = CompositingQuality.HighSpeed;
                        graphics.InterpolationMode = InterpolationMode.HighQualityBicubic;
                        graphics.CompositingMode = CompositingMode.SourceCopy;
                        graphics.DrawImage(image, 0, 0, width, height);
                        resized.Save(thumbnailPath, ImageFormat.Png);
                    }
                }
            }
            catch (Exception ex)
            {
                return false;
            }
            return true;
        }
        */

        public static bool MakeThumbnail(string filePath, string thumbnailPath, int width = 128, int height = 128)
        {
            try
            {
                using (Image<Rgba32> image = Image.Load(filePath))
                {
                    image.Mutate(x => x
                        .Resize(width, height)
                        .Grayscale());
                    image.Save(thumbnailPath);
                }
            }
            catch (Exception ex)
            {
                throw ex;
            }
            return true;
        }
    }
}
