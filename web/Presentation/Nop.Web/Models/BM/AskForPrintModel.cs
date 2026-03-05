
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using FluentValidation.Attributes;
using Nop.Web.Framework.Models;
using Nop.Web.Validators.BM;

namespace Nop.Web.Models.BM
{
    public partial class AskForPrintListModel : BaseNopModel
    {
        public AskForPrintListModel()
        {
            AskForPrints = new List<AskForPrintModel>();
            AskForPrintSave = new AskForPrintModel();
        }

        public List<AskForPrintModel> AskForPrints { get; set; }

        public AskForPrintModel AskForPrintSave { get; set; }
    }

    [Validator(typeof(AskForPrintValidator))]
    public partial class AskForPrintModel : BaseNopModel
    {
        public int Type { get; set; }

        public string ToCustomerName { get; set; }

        public int? ToCustomerId { get; set; }

        public string Phone { get; set; }

        [DataType(DataType.EmailAddress)]
        public string Email { get; set; }

        public string Identifier { get; set; }

        public string Title { get; set; }

        public string Message { get; set; }
    }
}
