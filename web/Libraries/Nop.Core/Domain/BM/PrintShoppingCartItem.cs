using System;

namespace Nop.Core.Domain.BM
{
    /// <summary>
    /// Represents a PrintShoppingCartItem
    /// </summary>
    public partial class PrintShoppingCartItem : BaseEntity
    { 
        public int ShoppingCartItemId { get; set; }

        public int PrintId { get; set; }

        public decimal Price { get; set; }

        public string ModelPath { get; set; }

        public int? ProductPictureId { get; set; }

        public DateTime CreatedDate { get; set; }

        public DateTime? UpdatedDate { get; set; }

        #region Navigation properties

        public virtual Print Print { get; set; }

        #endregion
    }
}