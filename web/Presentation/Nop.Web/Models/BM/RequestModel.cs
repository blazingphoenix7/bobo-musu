using System.Collections.Generic;
using FluentValidation.Attributes;
using Nop.Web.Framework.Models;
using Nop.Web.Validators.BM;

namespace Nop.Web.Models.BM
{
    [Validator(typeof(RequestValidator))]
    public partial class RequestModel : BaseNopEntityModel
    {
        public RequestModel()
        {
            MyPrints = new List<PrintModel>();
        }

        public int RequestId { get; set; }

        public string ToCustomerName { get; set; }

        public string Title { get; set; }

        public string Message { get; set; }

        public int ToCustomerId { get; set; }

        public int SharedPrintId { get; set; }

        public List<PrintModel> MyPrints { get; set; }
    }
}
