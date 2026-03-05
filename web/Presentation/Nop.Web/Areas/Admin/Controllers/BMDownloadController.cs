using System;
using System.IO;
using Microsoft.AspNetCore.Mvc;
using Nop.Web.Areas.Admin.Factories.BM;

namespace Nop.Web.Areas.Admin.Controllers
{
    public partial class BMDownloadController : BaseAdminController
    {
        #region Fields

        private readonly IDownloadModelFactory _downloadModelFactory;
      
        #endregion

        #region Ctor

        public BMDownloadController(IDownloadModelFactory downloadModelFactory)
        {
            _downloadModelFactory = downloadModelFactory;
        }

        #endregion

        #region Methods

        public virtual IActionResult Index(string type, int id)
        {
            var file = _downloadModelFactory.Download(type, id, out var fileName);
            var ext = Path.GetExtension(fileName);
            if (string.Equals(ext, ".zip", StringComparison.InvariantCultureIgnoreCase)) {
                return File(file, "application/zip", fileName);
            }
            else if (string.Equals(ext, ".plist", StringComparison.InvariantCultureIgnoreCase) ||
                     string.Equals(ext, ".txt", StringComparison.InvariantCultureIgnoreCase) ||
                     string.Equals(ext, ".xml", StringComparison.InvariantCultureIgnoreCase) ||
                     string.Equals(ext, ".json", StringComparison.InvariantCultureIgnoreCase))
            {
                return File(file, "text/plain", fileName);
            }

            return File(file, "image/jpeg", fileName);
        }

        #endregion
    }
}