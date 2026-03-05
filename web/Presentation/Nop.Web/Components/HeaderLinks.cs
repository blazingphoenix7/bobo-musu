using Microsoft.AspNetCore.Mvc;
using Nop.Web.Extensions;
using Nop.Web.Factories;
using Nop.Web.Framework.Components;

namespace Nop.Web.Components
{
    public class HeaderLinksViewComponent : NopViewComponent
    {
        private readonly ICommonModelFactory _commonModelFactory;

        public HeaderLinksViewComponent(ICommonModelFactory commonModelFactory)
        {
            this._commonModelFactory = commonModelFactory;
        }

        public IViewComponentResult Invoke(bool isEnabledInMobile = true)
        {
            var view = "Default";
            if (Request.IsMobileBrowser())
            {
                if (!isEnabledInMobile)
                    return Content(string.Empty);
                else
                    view = "Default";

            }
           
            var model = _commonModelFactory.PrepareHeaderLinksModel();
            return View(view, model);
        }
    }
}
