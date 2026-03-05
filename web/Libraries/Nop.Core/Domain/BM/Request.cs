using Nop.Core.Domain.Customers;
using System;
using System.Collections.Generic;

namespace Nop.Core.Domain.BM
{
    /// <summary>
    /// Represents a Request
    /// </summary>
    public partial class Request : BaseEntity
    { 
        public Request()
        {
            RequestHistories = new List<RequestHistory>();
        }
       
        public int CustomerId { get; set; }

        public int ToCustomerId { get; set; }

        public int RequestStatusId { get; set; }

        public DateTime CreatedDate { get; set; }

        public DateTime? UpdatedDate { get; set; }

        #region Navigation properties
        
        public List<RequestHistory> RequestHistories { get; set; }
        
        #endregion
    }
}