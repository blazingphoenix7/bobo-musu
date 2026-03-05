using Nop.Core.Domain.Customers;
using System;

namespace Nop.Core.Domain.BM
{
    /// <summary>
    /// Represents a Print
    /// </summary>
    public partial class Print : BaseEntity
    { 
        public Print()
        {
        }
       
        public string Name { get; set; }

        public int CustomerId { get; set; }

        public string ImagePath { get; set; }

        public string ThumbnailPath { get; set; }

        public string ModelPath { get; set; }

        public DateTime CreatedDate { get; set; }

        public DateTime? UpdatedDate { get; set; }

        public bool Deleted { get; set; }

        public string SharedBy { get; set; }

        #region Navigation properties

        public virtual Customer Customer { get; set; }
        
        #endregion
    }
}