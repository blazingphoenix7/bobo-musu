using Nop.Web.Framework.Models;

namespace Nop.Web.Areas.Admin.Models.BM
{
    public partial class PrintModel : BaseNopEntityModel
    {
         public string Name { get; set; }

         public string ThumbnailPath { get; set; }
    }
}
