using Nop.Web.Framework.Models;

namespace Nop.Web.Areas.Admin.Models.BM
{
    public partial class PrintOrderItemModel : BaseNopEntityModel
    {
        public int OrderItemId { get; set; }

        public PrintModel Print { get; set; }
        
        public string ModelPath { get; set; }

        public string ProductPictureThumbnailUrl { get; set; }
    }
}
