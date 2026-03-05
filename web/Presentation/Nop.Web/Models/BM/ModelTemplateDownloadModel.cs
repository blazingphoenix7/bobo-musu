using Nop.Web.Framework.Models;

namespace Nop.Web.Models.BM
{
    public partial class ModelTemplateDownloadModel : BaseNopEntityModel
    {
        public int CustomerId { get; set; }

        public int PrintId { get; set; }

        public int ProductId { get; set; }
    }
}
