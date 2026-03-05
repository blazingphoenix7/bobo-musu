using System;
using Nop.Core.Domain.Orders;

namespace Nop.Core.Domain.BM
{
    /// <summary>
    /// Represents a PrintOrderItem
    /// </summary>
    public partial class PrintOrderItem : BaseEntity
    { 
        public int OrderItemId { get; set; }

        public int PrintId { get; set; }

        public int? ProductPictureId { get; set; }

        public int Quantity { get; set; }

        public decimal UnitPriceInclTax { get; set; }

        public decimal UnitPriceExclTax { get; set; }

        public decimal PriceInclTax { get; set; }

        public decimal PriceExclTax { get; set; }

        public string ModelPath { get; set; }

        public DateTime CreatedDate { get; set; }

        public DateTime? UpdatedDate { get; set; }

        #region Navigation properties

        public virtual Print Print { get; set; }

        public virtual OrderItem OrderItem { get; set; }

        #endregion
    }
}