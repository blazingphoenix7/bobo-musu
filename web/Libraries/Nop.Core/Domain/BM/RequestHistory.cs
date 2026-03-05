using Nop.Core.Domain.Customers;
using System;

namespace Nop.Core.Domain.BM
{
    /// <summary>
    /// Represents a RequestHistory
    /// </summary>
    public partial class RequestHistory : BaseEntity
    { 
        public RequestHistory()
        {
        }
       
        public int RequestId { get; set; }

        public string Title { get; set; }

        public string Message { get; set; }

        public int RequestStatusId { get; set; }

        public DateTime CreatedDate { get; set; }

        public DateTime? UpdatedDate { get; set; }

        #region Navigation properties
        
        #endregion
    }
}