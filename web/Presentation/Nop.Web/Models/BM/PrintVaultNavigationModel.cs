using System.Collections.Generic;
using Nop.Web.Framework.Models;

namespace Nop.Web.Models.BM
{
    public partial class PrintVaultNavigationModel : BaseNopModel
    {
        public PrintVaultNavigationModel()
        {
            PrintVaultNavigationItems = new List<PrintVaultNavigationItemModel>();
        }

        public IList<PrintVaultNavigationItemModel> PrintVaultNavigationItems { get; set; }

        public PrintVaultNavigationEnum SelectedTab { get; set; }
    }

    public class PrintVaultNavigationItemModel : BaseNopModel
    {
        public string RouteName { get; set; }
        public string Title { get; set; }
        public PrintVaultNavigationEnum Tab { get; set; }
        public string ItemClass { get; set; }
    }

    public enum PrintVaultNavigationEnum
    {
        MyPrints = 0,
        SharedPrints = 10,
        PendingRequests = 20,
        AskForPrint = 30,
        Messages = 40
    }
}