using Microsoft.AspNetCore.Mvc;
using Nop.Web.Extensions;
using Nop.Web.Factories.BM;
using Nop.Web.Framework.Components;

namespace Nop.Web.Components
{
    public class BMNotification : NopViewComponent
    {
        private readonly IPrintModelFactory _printModelFactory;

        public BMNotification(IPrintModelFactory printModelFactory)
        {
            _printModelFactory = printModelFactory;
        }

        public IViewComponentResult Invoke()
        {
            var view = "Default";
            if (Request.IsMobileBrowser())
            {
                view = "BMMNotification";
            }
            var model = _printModelFactory.GetNotifications();
            return View(view, model);
        }
    }
}
