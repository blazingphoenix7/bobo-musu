using Nop.Web.Framework.Models;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;

namespace Nop.Web.Areas.Admin.Models.BM
{
    /// <summary>
    /// Represents a product model template model
    /// </summary>
    public partial class ProductModelTemplateModel : BaseNopEntityModel
    {
        #region Properties

        public ProductModelTemplateModel()
        {
            Upload = new UploadModel();
        }

        [UIHint("BMModelTemplateUpload")]
        [DisplayName("File")]
        public UploadModel Upload { get; set; }
        
        public int ProductId { get; set; }

        public string ModelTemplateFileName { get; set; }

        public int ModelTemplateTypeId { get; set; }

        public string ModelTemplateTypeName { get; set; }

        public string ModelTemplatePath { get; set; }

        public string ModelTemplateUrl { get; set; }

        public bool Active { get; set; }

        public class UploadModel
        {
            public int ProductId { get; set; }

            public string UploadPath { get; set; }
        }
        #endregion
    }
}