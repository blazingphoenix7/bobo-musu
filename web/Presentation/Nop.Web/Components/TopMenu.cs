using Microsoft.AspNetCore.Mvc;
using Nop.Web.Extensions;
using Nop.Web.Factories;
using Nop.Web.Framework.Components;

namespace Nop.Web.Components
{
    public class TopMenuViewComponent : NopViewComponent
    {
        private readonly ICatalogModelFactory _catalogModelFactory;

        public TopMenuViewComponent(ICatalogModelFactory catalogModelFactory)
        {
            this._catalogModelFactory = catalogModelFactory;
        }

        public IViewComponentResult Invoke(int? productThumbPictureSize)
        {
            var view = "Default";
            var model = _catalogModelFactory.PrepareTopMenuModel();
            if (Request.IsMobileBrowser())
            {
                view = "Default";
            }
            return View(view, model);
        }
    }
}
