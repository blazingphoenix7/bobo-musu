using Microsoft.AspNetCore.Mvc;
using Nop.Web.Extensions;
using Nop.Web.Factories;
using Nop.Web.Framework.Components;

namespace Nop.Web.Components
{
    public class LogoViewComponent : NopViewComponent
    {
        private readonly ICommonModelFactory _commonModelFactory;

        public LogoViewComponent(ICommonModelFactory commonModelFactory)
        {
            this._commonModelFactory = commonModelFactory;
        }

        public IViewComponentResult Invoke()
        {
            if (Request.IsMobileBrowser())
            {
                return Content(string.Empty);
            }
            var model = _commonModelFactory.PrepareLogoModel();
            return View(model);
        }
    }
}
