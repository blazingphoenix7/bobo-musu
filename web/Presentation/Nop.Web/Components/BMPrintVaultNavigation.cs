using Microsoft.AspNetCore.Mvc;
using Nop.Web.Extensions;
using Nop.Web.Factories.BM;
using Nop.Web.Framework.Components;

namespace Nop.Web.Components
{
    public class BMPrintVaultNavigation : NopViewComponent
    {
        private readonly IPrintModelFactory _printModelFactory;

        public BMPrintVaultNavigation(IPrintModelFactory printModelFactory)
        {
            _printModelFactory = printModelFactory;
        }

        public IViewComponentResult Invoke(int selectedTabId = 0)
        {
            //var view = "Default";
            //if (Request.IsMobileBrowser())
            //{
            //    view = "BMMPrintVaultNavigation";
            //}
            var model = _printModelFactory.PreparePrintVaultNavigationModel(selectedTabId);
            return View(model);
        }
    }
}
