using Microsoft.AspNetCore.Hosting;
using Nop.Core.Common;
using Nop.Services.BM;
using Nop.Services.Catalog;
using System;
using System.IO;
using System.IO.Compression;

namespace Nop.Web.Areas.Admin.Factories.BM
{
  public class DownloadModelFactory : IDownloadModelFactory
  {
    #region Fields

    private readonly IPrintService _printService;
    private readonly IProductService _productService;
    private readonly IHostingEnvironment _hostingEnvironment;

    #endregion

    #region Ctor

    public DownloadModelFactory(IPrintService printService,
                                IHostingEnvironment hostingEnvironment,
                                IProductService productService)
    {
      _printService = printService;
      _hostingEnvironment = hostingEnvironment;
      _productService = productService;
    }

    #endregion

    #region Methods

    public byte[] Download(string type, int id, out string fileName)
    {
      fileName = "";
      if (type == "printorder")
      {
        var printOrderItem = _printService.GetPrintOrderItem(id);
        if (printOrderItem == null)
          return null;

        var modelPath = printOrderItem.ModelPath;
        if (string.IsNullOrEmpty(modelPath))
        {
          throw new Exception("No ModelPath PrintOrderItemId: " + printOrderItem.Id);
        }
        modelPath = modelPath.StartsWith("/") ? modelPath.Substring(1) : modelPath;
        modelPath = Path.Combine(_hostingEnvironment.ContentRootPath, modelPath);
        if (!File.Exists(modelPath))
        {
          throw new Exception("Not Found ModelPath PrintOrderItemId: " + printOrderItem.Id);
        }

        var rootTempsPath = PrintPath.ROOT_TEMP; // $"Themes/BoBoMuSuTheme/Content/Temps";
        var zipFolderName = $"PrintOrder-{DateTime.UtcNow.Ticks}";
        var zipSourceFolder = Path.Combine(_hostingEnvironment.ContentRootPath, rootTempsPath, zipFolderName);
        if (!Directory.Exists(zipSourceFolder))
        {
          Directory.CreateDirectory(zipSourceFolder);
        }

        var zipModelPathFileName = Path.GetFileName(modelPath);
        File.Copy(modelPath, Path.Combine(zipSourceFolder, zipModelPathFileName));

        var zipDestPath = Path.Combine(_hostingEnvironment.ContentRootPath, rootTempsPath,
            $"{zipFolderName}.zip");
        ZipFile.CreateFromDirectory(zipSourceFolder, zipDestPath);
        fileName = $"{zipFolderName}.zip";
        return File.ReadAllBytes(zipDestPath);
      }
      else if (type == "modeltemplate")
      {
        var modelTemplate = _productService.GetProductModelTemplateById(id);
        if (modelTemplate == null)
          return null;

        var modelPath = modelTemplate.ModelTemplatePath;
        if (string.IsNullOrEmpty(modelPath))
        {
          throw new Exception("No ModelTemplatePath ProductModelTemplateId: " + modelTemplate.Id);
        }
        modelPath = modelPath.StartsWith("/") ? modelPath.Substring(1) : modelPath;
        modelPath = Path.Combine(_hostingEnvironment.ContentRootPath, modelPath);
        if (!File.Exists(modelPath))
        {
          throw new Exception("Not Found ModelTemplatePath ProductModelTemplateId: " + modelTemplate.Id);
        }

        if (string.Equals(Path.GetExtension(modelPath), ".3dm", StringComparison.InvariantCultureIgnoreCase))
        {
          var rootTempsPath = PrintPath.ROOT_TEMP; //$"Themes/BoBoMuSuTheme/Content/Temps";
          var zipFolderName = $"ModelTemplate-{DateTime.UtcNow.Ticks}";
          var zipSourceFolder =
              Path.Combine(_hostingEnvironment.ContentRootPath, rootTempsPath, zipFolderName);
          if (!Directory.Exists(zipSourceFolder))
          {
            Directory.CreateDirectory(zipSourceFolder);
          }

          var zipModelPathFileName = Path.GetFileName(modelPath);
          File.Copy(modelPath, Path.Combine(zipSourceFolder, zipModelPathFileName));

          var zipDestPath = Path.Combine(_hostingEnvironment.ContentRootPath, rootTempsPath,
              $"{zipFolderName}.zip");
          ZipFile.CreateFromDirectory(zipSourceFolder, zipDestPath);
          fileName = $"{zipFolderName}.zip";
          return File.ReadAllBytes(zipDestPath);
        }
        else
        {
          fileName = Path.GetFileName(modelPath);
          return File.ReadAllBytes(modelPath);
        }
      }

      return null;
    }

    #endregion
  }
}
