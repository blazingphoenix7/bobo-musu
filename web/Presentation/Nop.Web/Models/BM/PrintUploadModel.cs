using Nop.Web.Framework.Models;

namespace Nop.Web.Models.BM
{
    public partial class PrintUploadModel : BaseNopEntityModel
    {
        public int CustomerId { get; set; }

        public string Name { get; set; }
    }
}
