namespace Nop.Core.Domain.BM
{
    /// <summary>
    /// Represents a PrintProductPicture
    /// </summary>
    public partial class PrintProductPicture : BaseEntity
    {
        public int PrintId { get; set; }

        public int? ProductPictureId { get; set; }
    }
}