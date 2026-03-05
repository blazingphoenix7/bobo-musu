using System;

namespace Nop.Core.Domain.BM
{
    /// <summary>
    /// Represents a ProductModelTemplate
    /// </summary>
    public partial class ProductModelTemplate : BaseEntity
    { 
        public int ProductId { get; set; }

        public string ModelTemplatePath { get; set; }

        public int ModelTemplateTypeId { get; set; }

        public bool Active { get; set; }

        public DateTime CreatedDate { get; set; }

        public DateTime? UpdatedDate { get; set; }

        #region Navigation properties

        #endregion
    }
}