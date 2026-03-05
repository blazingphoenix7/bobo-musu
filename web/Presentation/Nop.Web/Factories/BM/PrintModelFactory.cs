
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Nop.Core;
using Nop.Core.Common;
using Nop.Core.Domain.BM;
using Nop.Core.Domain.Customers;
using Nop.Services.BM;
using Nop.Services.Catalog;
using Nop.Services.Customers;
using Nop.Services.Orders;
using Nop.Web.Extensions;
using Nop.Web.Framework.Themes;
using Nop.Web.Models.BM;
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;

namespace Nop.Web.Factories.BM
{
  public class PrintModelFactory : IPrintModelFactory
  {
    #region Fields

    private readonly IWorkContext _workContext;
    private readonly IThemeContext _themeContext;
    private readonly ICustomerService _customerService;
    private readonly IPrintService _printService;
    private readonly IHostingEnvironment _hostingEnvironment;
    private readonly IProductService _productService;
    private readonly IShoppingCartService _shoppingCartService;

    #endregion

    #region Ctor

    public PrintModelFactory(IWorkContext workContext,
                             ICustomerService customerService,
                             IPrintService printService,
                             IThemeContext themeContext,
                             IHostingEnvironment hostingEnvironment,
                             IProductService productService,
                             IShoppingCartService shoppingCartService)
    {
      _workContext = workContext;
      _customerService = customerService;
      _printService = printService;
      _themeContext = themeContext;
      _hostingEnvironment = hostingEnvironment;
      _productService = productService;
      _shoppingCartService = shoppingCartService;
    }

    #endregion

    public MessageListModel GetMessages()
    {
      var result = new MessageListModel();
      var currentCustomer = _workContext.CurrentCustomer;
      var requests = _printService.GetAllRequests(currentCustomer.Id);
      foreach (var request in requests)
      {
        var requestHistory = request.RequestHistories.FirstOrDefault();
        if (requestHistory == null) continue;
        PrintModel acceptedPrint = null;
        var fromCustomerName = "";
        if (request.RequestStatusId == (int)RequestStatus.Pending)
        {
          fromCustomerName = _customerService.GetCustomerFullName(new Customer() { Id = request.CustomerId });
        }
        else if (request.RequestStatusId == (int)RequestStatus.Accept)
        {
          fromCustomerName = _customerService.GetCustomerFullName(new Customer() { Id = request.ToCustomerId });
          var print = _printService.GetPrintByRequestId(request.Id);
          if (print != null)
            acceptedPrint = new PrintModel()
            {
              Id = print.Id,
              Name = print.Name,
              ThumbnailPath = print.ThumbnailPath
            };
        }
        result.Messages.Add(new MessageModel()
        {
          RequestId = request.Id,
          RequestStatusId = request.RequestStatusId,
          Title = requestHistory.Title,
          Message = requestHistory.Message,
          FromCustomerName = fromCustomerName,
          CustomerId = request.CustomerId,
          ToCustomerId = request.ToCustomerId,
          AcceptedPrint = acceptedPrint
        });
      }

      return result;
    }

    public List<AskForPrintModel> GetAskForPrints()
    {
      /*
      var registeredRole = _customerService.GetCustomerRoleBySystemName(NopCustomerDefaults.RegisteredRoleName);
      var selectedCustomerRoleIds = new List<int>();
      if (registeredRole != null)
          selectedCustomerRoleIds.Add(registeredRole.Id);
      var customers = _customerService.GetAllCustomers(customerRoleIds: selectedCustomerRoleIds.ToArray()).Where(m=>!m.Deleted).ToList();
      var currentCustomer = _workContext.CurrentCustomer;
      var items = new List<AskForPrintModel>();
      foreach (var customer in customers)
      {
          if(customer.Id == currentCustomer.Id) continue; // Ingore myself

          items.Add(new AskForPrintModel()
          {
              Type = (int)AskForPrintType.Internal,
              ToCustomerId = customer.Id,
              Email = customer.Email,
              ToCustomerName = _customerService.GetCustomerFullName(customer)
          });
      }

      return items.OrderBy(m=>m.ToCustomerName).ToList();
      */
      return new List<AskForPrintModel>();
    }

    public MyPrintListModel GetPrints()
    {
      var result = new MyPrintListModel();
      var currentCustomer = _workContext.CurrentCustomer;
      var prints = _printService.GetPrints(currentCustomer.Id);
      foreach (var print in prints)
      {
        result.Prints.Add(new PrintModel()
        {
          Id = print.Id,
          Name = print.Name,
          ThumbnailPath = print.ThumbnailPath
        });
      }
      return result;
    }

    public bool AddAskForPrint(AskForPrintModel askForPrintSave, out string message)
    {
      message = "";
      var currentCustomer = _workContext.CurrentCustomer;
      var toCustomer = _customerService.GetCustomerByEmail(askForPrintSave.Email);
      if (toCustomer != null)
      {
        /*if (toCustomer.Email == currentCustomer.Email)
        {
            message = "You can't send the request for yourself";
            return false;
        }*/
        _printService.AddAskForPrint(currentCustomer.Id, toCustomer.Id, askForPrintSave.Title, askForPrintSave.Message);
      }
      else
      {
        _printService.AddAskForPrintExternal(currentCustomer.Id,
                                            askForPrintSave.ToCustomerName,
                                            askForPrintSave.Phone,
                                            askForPrintSave.Email,
                                            askForPrintSave.Identifier,
                                            askForPrintSave.Type,
                                            askForPrintSave.Title,
                                            askForPrintSave.Message);
      }

      return true;
    }

    public void AcceptPendingRequest(RequestModel pendingRequestAccept)
    {
      var currentCustomer = _workContext.CurrentCustomer;
      _printService.AcceptPendingRequest(currentCustomer.Id,
                                         pendingRequestAccept.ToCustomerId,
                                         pendingRequestAccept.SharedPrintId,
                                         pendingRequestAccept.RequestId,
                                         pendingRequestAccept.Title,
                                         pendingRequestAccept.Message);
    }

    public RequestModel PrepareAcceptPendingRequest(int requestId, int toCustomerId)
    {
      var request = _printService.GetPendingRequestById(requestId);
      if (request == null) return null;

      var currentCustomer = _workContext.CurrentCustomer;
      var title = request.RequestHistories.First().Title;
      var result = new RequestModel();
      result.ToCustomerId = toCustomerId;
      result.RequestId = requestId;
      result.ToCustomerName = _customerService.GetCustomerFullName(new Customer() { Id = toCustomerId });
      result.Title = $"{result.ToCustomerName}'s request for {title}'s print";
      result.Message = $@"Click the 'Take a Print' button to take a picture of {title}'s print{Environment.NewLine}{Environment.NewLine}" +
                        $"Then Select their Print from the drop down menu and click 'Submit'{Environment.NewLine}{Environment.NewLine}" +
                        "If you have any trouble, click on the 'HOW IT WORKS' bar at the bottom of the screen.";
      var prints = _printService.GetPrints(currentCustomer.Id);
      foreach (var print in prints)
      {
        result.MyPrints.Add(new PrintModel()
        {
          Id = print.Id,
          Name = print.Name,
          ThumbnailPath = print.ThumbnailPath
        });
      }
      return result;
    }

    public void DeletePendingRequest(int requestId)
    {
      _printService.DeleteRequest(requestId);
    }

    public MyPrintListModel GetSharedPrints()
    {
      var result = new MyPrintListModel();
      var currentCustomer = _workContext.CurrentCustomer;
      var prints = _printService.GetSharedPrints(currentCustomer.Id);
      foreach (var print in prints)
      {
        result.Prints.Add(new PrintModel()
        {
          Id = print.Id,
          Name = print.Name,
          ThumbnailPath = print.ThumbnailPath,
          SharedBy = print.SharedBy
        });
      }
      return result;
    }

    public void DeleteMessage(int requestId)
    {
      _printService.DeleteRequest(requestId);
    }

    public int UploadPrint(PrintUploadModel printUpload)
    {
      var customer = _customerService.GetCustomerById(printUpload.CustomerId);
      if (customer == null)
      {
        throw new Exception("Invalid Customer!");
      }
      if (printUpload.Form?.Files == null || printUpload.Form.Files.Count == 0)
      {
        throw new Exception("File(s) not found to upload!");
      }
      if (string.IsNullOrEmpty(printUpload.Name))
      {
        throw new Exception("Name required!");
      }
      var rootPath = string.Format(PrintPath.ROOT, customer.Id);
      var rootRelativePath = string.Format(PrintPath.RELATIVE, customer.Id);
      var rootPhysicalFolder = Path.Combine(_hostingEnvironment.ContentRootPath, rootPath);
      if (!Directory.Exists(rootPhysicalFolder))
      {
        Directory.CreateDirectory(rootPhysicalFolder);
      }
      var imagePhysicalFolder = Path.Combine(rootPhysicalFolder, PrintPath.IMAGES);
      if (!Directory.Exists(imagePhysicalFolder))
      {
        Directory.CreateDirectory(imagePhysicalFolder);
      }
      var thumbPhysicalFolder = Path.Combine(rootPhysicalFolder, PrintPath.THUMBS);
      if (!Directory.Exists(thumbPhysicalFolder))
      {
        Directory.CreateDirectory(thumbPhysicalFolder);
      }
      var modelPhysicalFolder = Path.Combine(rootPhysicalFolder, PrintPath.MODELS);
      if (!Directory.Exists(modelPhysicalFolder))
      {
        Directory.CreateDirectory(modelPhysicalFolder);
      }
      var imagePath = "";
      var thumbnailPath = "";
      var modelPath = "";
      var relativeImagePath = "";
      var relativeThumbnailPath = "";
      var relativeModelPath = "";
      foreach (var file in printUpload.Form.Files)
      {
        if (file.Length == 0)
          throw new Exception("File(s) not found to upload!");

        if (file.ContentType.Contains("image"))
        {
          var imagePhysicalPath = FileExtensions.GetUniqueFilePath(Path.Combine(imagePhysicalFolder, file.FileName));
          imagePath = Path.Combine(rootPath, PrintPath.IMAGES, Path.GetFileName(imagePhysicalPath));
          relativeImagePath = Path.Combine(rootRelativePath, PrintPath.IMAGES, Path.GetFileName(imagePhysicalPath));
          using (var stream = new FileStream(imagePhysicalPath, FileMode.Create))
          {
            file.CopyTo(stream);
          }
          var thumbPhysicalPath = FileExtensions.GetUniqueFilePath(Path.Combine(thumbPhysicalFolder, $"{Path.GetFileNameWithoutExtension(file.FileName)}.jpg"));
          if (ImageProcessorExtensions.MakeThumbnail(imagePhysicalPath, thumbPhysicalPath))
          {
            thumbnailPath = Path.Combine(rootPath, PrintPath.THUMBS, Path.GetFileName(thumbPhysicalPath));
            relativeThumbnailPath = Path.Combine(rootRelativePath, PrintPath.THUMBS, Path.GetFileName(imagePhysicalPath));

          }
        }
        //This uploads .3dm files manually..
        else if (Path.GetExtension(file.FileName).Equals(".3dm", StringComparison.InvariantCultureIgnoreCase))
        {
          var modelPhysicalPath = FileExtensions.GetUniqueFilePath(Path.Combine(modelPhysicalFolder, $"{file.FileName}"));
          modelPath = Path.Combine(rootPath, PrintPath.MODELS, Path.GetFileName(modelPhysicalPath));
          relativeModelPath = Path.Combine(rootRelativePath, PrintPath.MODELS, Path.GetFileName(modelPhysicalPath));
          using (var stream = new FileStream(modelPhysicalPath, FileMode.Create))
          {
            file.CopyTo(stream);
          }
        }
      }
      var print = new Print()
      {
        CustomerId = customer.Id,
        Name = printUpload.Name,
        ImagePath = relativeImagePath,
        ThumbnailPath = relativeThumbnailPath,
        ModelPath = relativeModelPath,
        CreatedDate = DateTime.UtcNow,
        UpdatedDate = DateTime.UtcNow
      };
      _printService.AddPrint(print);

      return print.Id;
    }

    public void DeletePrint(int printId)
    {
      _printService.DeletePrint(printId);
    }

    public byte[] DownloadModelTemplate(ModelTemplateDownloadModel modelTemplateDownload, out string zipFileName)
    {
      var customer = _customerService.GetCustomerById(modelTemplateDownload.CustomerId);
      if (customer == null)
      {
        throw new Exception("Invalid Customer!");
      }
      var print = _printService.GetPrints(customer.Id).FirstOrDefault(m => m.Id == modelTemplateDownload.PrintId);
      if (print == null)
      {
        throw new Exception("Invalid Print!");
      }
      var product = _productService.GetProductById(modelTemplateDownload.ProductId);
      if (product == null)
      {
        throw new Exception("Invalid Product!");
      }

      var printImagePath = print.ImagePath;
      if (string.IsNullOrEmpty(printImagePath))
      {
        throw new Exception("Finger image is invalid for print with ID: " + print.Id);
      }
      printImagePath = printImagePath.StartsWith("/") ? printImagePath.Substring(1) : printImagePath;
      printImagePath = Path.Combine(_hostingEnvironment.ContentRootPath, printImagePath);
      if (!File.Exists(printImagePath))
      {
        throw new Exception("Finger image not found for print with ID: " + print.Id);
      }

      var modelTemplates = _productService.GetProductModelTemplatesByProductId(product.Id);
      if (modelTemplates.Count == 0)
      {
        throw new Exception("No model templates found for product with ID: " + product.Id);
      }

      var modelTemplate = modelTemplates.FirstOrDefault(m => m.ModelTemplateTypeId == (int)ModelTemplateType.Template && m.Active);
      if (modelTemplate == null)
      {
        throw new Exception("Please Add/Activate a product model in template for product with ID: " + product.Id);
      }
      var modelTemplatePath = modelTemplate.ModelTemplatePath;
      modelTemplatePath = modelTemplatePath.StartsWith("/") ? modelTemplatePath.Substring(1) : modelTemplatePath;
      modelTemplatePath = Path.Combine(_hostingEnvironment.ContentRootPath, modelTemplatePath);
      if (!File.Exists(modelTemplatePath))
      {
        throw new Exception("No model templates found for product with ID: " + product.Id);
      }

      modelTemplate = modelTemplates.FirstOrDefault(m => m.ModelTemplateTypeId == (int)ModelTemplateType.Config && m.Active);
      if (modelTemplate == null)
      {
        throw new Exception("Please Add/Activate a product model in template for product with ID: " + product.Id);
      }
      var configPath = modelTemplate.ModelTemplatePath;
      configPath = configPath.StartsWith("/") ? configPath.Substring(1) : configPath;
      configPath = Path.Combine(_hostingEnvironment.ContentRootPath, configPath);
      if (!File.Exists(configPath))
      {
        throw new Exception("No model templates found in Config for product with ID: " + product.Id);
      }

      modelTemplate = modelTemplates.FirstOrDefault(m => m.ModelTemplateTypeId == (int)ModelTemplateType.Mask && m.Active);
      var maskPath = string.Empty;
      if (modelTemplate != null)
      {
        maskPath = modelTemplate.ModelTemplatePath;
        maskPath = maskPath.StartsWith("/") ? maskPath.Substring(1) : maskPath;
        maskPath = Path.Combine(_hostingEnvironment.ContentRootPath, maskPath);
        if (!File.Exists(maskPath))
        {
          throw new Exception("No model templates found for product with ID: " + product.Id);
        }
      }

      var rootTempsPath = PrintPath.ROOT_TEMP;
      var zipFolderName = $"ModelTemplate-{DateTime.UtcNow.Ticks}";
      var zipSourceFolder = Path.Combine(_hostingEnvironment.ContentRootPath, rootTempsPath, zipFolderName);
      if (!Directory.Exists(zipSourceFolder))
      {
        Directory.CreateDirectory(zipSourceFolder);
      }

      var zipPrintImageFileName = "finger.jpg";
      File.Copy(printImagePath, Path.Combine(zipSourceFolder, zipPrintImageFileName));

      var zipTemplateFileName = "template.3dm";
      File.Copy(modelTemplatePath, Path.Combine(zipSourceFolder, zipTemplateFileName));

      var zipConfigFileName = "config.plist";
      File.Copy(configPath, Path.Combine(zipSourceFolder, zipConfigFileName));

      if (!string.IsNullOrEmpty(maskPath))
      {
        var zipMaskFileName = "mask.png";
        File.Copy(maskPath, Path.Combine(zipSourceFolder, zipMaskFileName));
      }

      var zipDestPath = Path.Combine(_hostingEnvironment.ContentRootPath, rootTempsPath, $"{zipFolderName}.zip");

      ZipFile.CreateFromDirectory(zipSourceFolder, zipDestPath);

      zipFileName = $"{zipFolderName}.zip";

      return File.ReadAllBytes(zipDestPath);
    }

    public void UploadPrintShoppingCartItem(Customer customer, PrintShoppingCartItem printShoppingCartItem, IFormCollection form)
    {
      if (printShoppingCartItem == null) return;

      var rootPath = string.Format(PrintPath.ROOT_ORDER, customer.Id);
      var modelPhysicalFolder = Path.Combine(_hostingEnvironment.ContentRootPath, rootPath);
      if (!Directory.Exists(modelPhysicalFolder))
      {
        Directory.CreateDirectory(modelPhysicalFolder);
      }
      var modelPath = "";
      foreach (var file in form.Files)
      {
        if (file.Length == 0)
          return;

        if (Path.GetExtension(file.FileName).Equals(".3dm", StringComparison.InvariantCultureIgnoreCase))
        {
          var modelPhysicalPath = FileExtensions.GetUniqueFilePath(Path.Combine(modelPhysicalFolder, file.FileName));
          modelPath = Path.Combine(rootPath, Path.GetFileName(modelPhysicalPath));
          using (var stream = new FileStream(modelPhysicalPath, FileMode.Create))
          {
            file.CopyTo(stream);
          }
        }
      }
      printShoppingCartItem.ModelPath = modelPath;
      printShoppingCartItem.UpdatedDate = DateTime.UtcNow;
      _shoppingCartService.UpdatePrintShoppingCartItem(printShoppingCartItem);
    }

    public PrintVaultNavigationModel PreparePrintVaultNavigationModel(int selectedTabId = 0)
    {
      var model = new PrintVaultNavigationModel();

      model.PrintVaultNavigationItems.Add(new PrintVaultNavigationItemModel
      {
        RouteName = "BMMyPrints",
        Title = "My Prints",
        Tab = PrintVaultNavigationEnum.MyPrints,
        ItemClass = "my-prints"
      });

      //model.PrintVaultNavigationItems.Add(new PrintVaultNavigationItemModel
      //{
      //  RouteName = "BMMessages",
      //  Title = "Messages",
      //  Tab = PrintVaultNavigationEnum.Messages,
      //  ItemClass = "messages"
      //});

      model.PrintVaultNavigationItems.Add(new PrintVaultNavigationItemModel
      {
        RouteName = "BMAskForPrint",
        Title = "Request a Print",
        Tab = PrintVaultNavigationEnum.AskForPrint,
        ItemClass = "ask-for-print"
      });

      model.PrintVaultNavigationItems.Add(new PrintVaultNavigationItemModel
      {
        RouteName = "BMSharedPrints",
        Title = "Shared Prints",
        Tab = PrintVaultNavigationEnum.SharedPrints,
        ItemClass = "shared-prints"
      });


      model.SelectedTab = (PrintVaultNavigationEnum)selectedTabId;
      return model;
    }

    public List<string> GetNotifications()
    {
      var messages = new List<string>();
      var isRegistered = _workContext.CurrentCustomer.IsRegistered();
      if (isRegistered)
      {
        var count = _printService.GetPendingRequests(_workContext.CurrentCustomer.Id).Count;
        if (count > 0)
          messages.Add($"<a href='/print/messagelist'>{count} pending request(s)</a>");
      }

      return messages;
    }

    public void SaveDebug(string file, string content)
    {
      var rootPath = $"{PrintPath.ROOT_TEMP}/Debug";

      if (!Directory.Exists(rootPath))
        Directory.CreateDirectory(rootPath);

      var filePath = Path.Combine(rootPath, file.Replace(" ", "") + DateTime.Now.Ticks + ".txt");
      File.WriteAllText(filePath, content);
    }
  }
}
