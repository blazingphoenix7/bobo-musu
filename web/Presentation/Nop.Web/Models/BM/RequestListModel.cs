using Nop.Web.Framework.Models;
using System.Collections.Generic;

namespace Nop.Web.Models.BM
{
    public partial class RequestListModel : BaseNopModel
    {
        public RequestListModel()
        {
            Requests = new List<RequestModel>();
        }

        public List<RequestModel> Requests { get; set; }
    }
}
