using Nop.Web.Framework.Models;
using System.Collections.Generic;

namespace Nop.Web.Models.BM
{
    public partial class MyPrintListModel : BaseNopModel
    {
        public MyPrintListModel()
        {
            Prints = new List<PrintModel>();
        }

        public List<PrintModel> Prints { get; set; }
    }
}
