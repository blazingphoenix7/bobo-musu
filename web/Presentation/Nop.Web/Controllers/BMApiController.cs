using Microsoft.AspNetCore.Mvc;
using Nop.Web.Factories.BM;
using Nop.Web.Models.BM;
using System;
using System.Linq;
using Nop.Core.Domain.Orders;
using Nop.Core.Http.Extensions;
using Nop.Services.Authentication;

namespace Nop.Web.Controllers
{
  [Route("api/[action]")]
  [ApiController]
  public class BMApiController : ControllerBase
  {
    #region Fields

    private readonly IPrintModelFactory _printModelFactory;

    #endregion

    #region Ctor

    public BMApiController(IPrintModelFactory printModelFactory)
    {
      _printModelFactory = printModelFactory;
    }

    #endregion

    #region Methods

    [HttpPost]
    public IActionResult InitiateApp([FromBody] DeviceInfoModel deviceInfo)
    {
      try
      {
        if (deviceInfo == null)
        {
          var r = new ApiResponse<object>
          (
              statusCode: (int)ApiStatusCode.Error,
              errorMessage: "Device information not found!"
          );

          return new JsonResult(r);
        }

        if (deviceInfo.Type == DeviceType.Web)
        {
          var r = new ApiResponse<object>
          (
              statusCode: (int)ApiStatusCode.Error,
              errorMessage: "Web initiation is not implemented yet!"
          );
          return new JsonResult(r);
        }

        //SET DeviceInfo in the Session.
        HttpContext.Session.Set("DeviceInfo", deviceInfo);

        //return Success Result only if it is initiated of native app.
        var result = new ApiResponse<object>
        (
            statusCode: (int)ApiStatusCode.Success
        );
        return new JsonResult(result);
      }
      catch (Exception ex)
      {
        var result = new ApiResponse<object>
        (
            statusCode: (int)ApiStatusCode.Error,
            errorMessage: ex.Message
        );
        return new JsonResult(result);
      }
    }

    [HttpPost]
    public IActionResult UploadPrint([FromBody] PrintUploadModel printUpload)
    {
      try
      {
        var printId = _printModelFactory.UploadPrint(printUpload);
        var result = new ApiResponse<object>
        (
            statusCode: (int)ApiStatusCode.Success,
            data: new { printid = printId }
        );
        return new JsonResult(result);
      }
      catch (Exception ex)
      {
        var result = new ApiResponse<object>
        (
            statusCode: (int)ApiStatusCode.Error,
            errorMessage: ex.Message
        );
        return new JsonResult(result);
      }
    }

    [HttpPost]
    public IActionResult DownloadModelTemplate([FromBody] ModelTemplateDownloadModel modelTemplateDownload)
    {
      try
      {
        var file = _printModelFactory.DownloadModelTemplate(modelTemplateDownload, out var zipFileName);
        return File(file, "application/zip", zipFileName);
      }
      catch (Exception ex)
      {
        var result = new ApiResponse<object>
        (
            statusCode: (int)ApiStatusCode.Error,
            errorMessage: ex.Message
        );
        return new JsonResult(result);
      }

    }
    #endregion
  }

  public partial class ShoppingCartController : BasePublicController
  {
    private readonly IPrintModelFactory _printModelFactory;

    // api/addtocart
    [HttpPost]
    public IActionResult AddToCart([FromBody] AddToCardModel model)
    {
      try
      {
        var customer = _customerService.GetCustomerById(model.CustomerId);
        _workContext.CurrentCustomer = customer;
        var actionResult = this.AddProductToCart_Details(model.ProductId, (int)ShoppingCartType.ShoppingCart, model.Form);
        var value = (dynamic)((JsonResult)actionResult).Value;
        var success = Convert.ToBoolean(value.success);
        if (success)
        {
          var printShoppingCartItem = _workContext.CurrentCustomer.ShoppingCartItems.First().PrintShoppingCartItems.FirstOrDefault();
          _printModelFactory.UploadPrintShoppingCartItem(customer, printShoppingCartItem, model.Form);
        }
        var result = new ApiResponse<object>
        (
            statusCode: success ? (int)ApiStatusCode.Success : (int)ApiStatusCode.Error,
            errorMessage: !success ? Convert.ToString(value.message) : ""
        );

        return new JsonResult(result);
      }
      catch (Exception ex)
      {
        var result = new ApiResponse<object>
        (
            statusCode: (int)ApiStatusCode.Error,
            errorMessage: ex.Message
        );
        return new JsonResult(result);
      }
    }

  }
}
