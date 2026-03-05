using System;

namespace Nop.Core.Domain.BM
{
    /// <summary>
    /// Represents a ExternalRequestMessage
    /// </summary>
    public partial class ExternalRequestMessage : BaseEntity
    { 
        public ExternalRequestMessage()
        {
        }
       
        public int ExternalRequestId { get; set; }

        public string Title { get; set; }

        public string Message { get; set; }
        
        public DateTime CreatedDate { get; set; }

        public DateTime? UpdatedDate { get; set; }

        #region Navigation properties

        #endregion
    }
}