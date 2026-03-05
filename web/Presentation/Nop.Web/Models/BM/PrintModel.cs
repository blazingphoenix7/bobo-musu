using Nop.Web.Framework.Models;
using System.ComponentModel.DataAnnotations.Schema;

namespace Nop.Web.Models.BM
{
  public partial class PrintModel : BaseNopEntityModel
  {
    public string Name { get; set; }

    public string ThumbnailPath { get; set; }

    [NotMapped]
    public string ImagePath { get; set; }

    public string SharedBy { get; set; }
  }
}
