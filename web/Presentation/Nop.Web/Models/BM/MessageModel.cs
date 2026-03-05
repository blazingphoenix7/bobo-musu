using Nop.Web.Framework.Models;

namespace Nop.Web.Models.BM
{
    public partial class MessageModel : BaseNopEntityModel
    {
        public int RequestId { get; set; }

        public int CustomerId { get; set; }

        public int ToCustomerId { get; set; }

        public string FromCustomerName { get; set; }

        public string Title { get; set; }

        public string Message { get; set; }
        
        public int RequestStatusId { get; set; }

        public PrintModel AcceptedPrint { get; set; }
    }
}
