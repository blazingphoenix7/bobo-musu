using Microsoft.AspNetCore.Mvc;
using Nop.Web.Extensions;
using Nop.Web.Factories.BM;
using Nop.Web.Framework.Components;

namespace Nop.Web.Components
{
    public class BMFilter : NopViewComponent
    {
        private readonly IPrintModelFactory _printModelFactory;

        public BMFilter(IPrintModelFactory printModelFactory)
        {
            _printModelFactory = printModelFactory;
        }

        public IViewComponentResult Invoke()
        {
            var view = "Default";
            if (Request.IsMobileBrowser())
            {
                view = "BMMFilter";
            }
            return View(view);
        }
    }
}
