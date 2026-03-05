using Microsoft.AspNetCore.Mvc;
using Nop.Web.Framework.Mvc.Filters;
using Nop.Web.Framework.Security;
using Nop.Core.Http.Extensions;
using Nop.Web.Models.BM;
using Nop.Core;
using Nop.Core.Domain.Customers;
using Nop.Web.Extensions;

namespace Nop.Web.Controllers
{
  public partial class HomeController : BasePublicController
  {
    private readonly IWorkContext _workContext;

    public HomeController(IWorkContext workContext)
    {
      _workContext = workContext;
    }

    [HttpsRequirement(SslRequirement.No)]
    public virtual IActionResult Index(bool allowHome = false)
    {
      ////var deviceInfo = HttpContext.Session.Get<DeviceInfoModel>("DeviceInfo");

      ////if (deviceInfo == null
      ////   || deviceInfo.Type == DeviceType.Web)
      ////  return View();

      //if (!_workContext.CurrentCustomer.IsRegistered()
      //    && Request.IsMobileBrowser())
      //{
      //  return RedirectToAction("Welcome", "BMHome");
      //}
      //else
      //{
      // return View();
      //}
      if(_workContext.CurrentCustomer.IsRegistered()
         || allowHome)
        return View();

      if (!_workContext.CurrentCustomer.IsRegistered()
          && Request.IsMobileBrowser())
        return RedirectToAction("Login", "Customer");
        //return RedirectToAction("Welcome", "BMHome");

        return View();
    }
  }
}