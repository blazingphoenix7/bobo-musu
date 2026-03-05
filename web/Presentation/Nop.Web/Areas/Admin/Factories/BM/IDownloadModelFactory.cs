namespace Nop.Web.Areas.Admin.Factories.BM
{
    public interface IDownloadModelFactory
    {
        byte[] Download(string type, int id, out string fileName);
    }
}
