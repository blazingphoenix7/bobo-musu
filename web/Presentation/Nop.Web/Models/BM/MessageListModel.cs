using Nop.Web.Framework.Models;
using System.Collections.Generic;

namespace Nop.Web.Models.BM
{
    public partial class MessageListModel : BaseNopModel
    {
        public MessageListModel()
        {
            Messages = new List<MessageModel>();
        }

        public List<MessageModel> Messages { get; set; }
    }
}
