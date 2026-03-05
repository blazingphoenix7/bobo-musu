using Nop.Web.Framework.Models;

namespace Nop.Web.Areas.Admin.Models.BM
{
    /// <summary>
    /// Represents a product model template search model
    /// </summary>
    public partial class ProductModelTemplateSearchModel : BaseSearchModel
    {
        #region Properties

        public int ProductId { get; set; }
        
        #endregion
    }
}