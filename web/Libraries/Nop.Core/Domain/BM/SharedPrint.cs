using Nop.Core.Domain.Customers;
using System;

namespace Nop.Core.Domain.BM
{
    /// <summary>
    /// Represents a SharedPrint
    /// </summary>
    public partial class SharedPrint : BaseEntity
    { 
        public SharedPrint()
        {
        }
       
        public int PrintId { get; set; }

        public int? RequestId { get; set; }

        public int CustomerId { get; set; }

        public int ToCustomerId { get; set; }

        public DateTime CreatedDate { get; set; }

        public DateTime? UpdatedDate { get; set; }

        #region Navigation properties

        public virtual Print Print { get; set; }
        
        #endregion
    }
}