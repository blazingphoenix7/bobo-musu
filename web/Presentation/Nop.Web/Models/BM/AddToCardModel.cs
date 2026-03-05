using Nop.Web.Framework.Models;

namespace Nop.Web.Models.BM
{
    public class AddToCardModel : BaseNopEntityModel
    {
        public int CustomerId { get; set; }

        public int ProductId { get; set; }

        public int PrintId { get; set; }
    }
}
