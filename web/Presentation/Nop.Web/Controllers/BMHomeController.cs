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
  public class BMHomeController : BasePublicController
  {
    private readonly IWorkContext _workContext;

    public BMHomeController(IWorkContext workContext)
    {
      _workContext = workContext;
    }

    [HttpsRequirement(SslRequirement.No)]
    public IActionResult Welcome()
    {
      //Totally inversed condition than Home > Index ActionResult Method
      if (!_workContext.CurrentCustomer.IsRegistered()
          && Request.IsMobileBrowser())
      {
        return RedirectToAction("Login", "Customer");
        //return View();
      }
      else
      {
        return RedirectToAction("Index", "Home");
      }
    }
  }
}