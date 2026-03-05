
using System.Collections.Generic;
using Microsoft.AspNetCore.Http;
using Nop.Core.Domain.BM;
using Nop.Core.Domain.Customers;
using Nop.Web.Models.BM;

namespace Nop.Web.Factories.BM
{
    public partial interface IPrintModelFactory
    {
        MessageListModel GetMessages();

        List<AskForPrintModel> GetAskForPrints();

        MyPrintListModel GetPrints();

        bool AddAskForPrint(AskForPrintModel askForPrintSave, out string message);

        void AcceptPendingRequest(RequestModel pendingRequestAccept);

        RequestModel PrepareAcceptPendingRequest(int requestId, int toCustomerId);

        void DeletePendingRequest(int requestId);

        MyPrintListModel GetSharedPrints();

        void DeleteMessage(int requestId);

        int UploadPrint(PrintUploadModel printUpload);

        void DeletePrint(int printId);

        byte[] DownloadModelTemplate(ModelTemplateDownloadModel modelTemplateDownload, out string zipFileName);

        void UploadPrintShoppingCartItem(Customer customer, PrintShoppingCartItem printShoppingCartItem, IFormCollection form);

        PrintVaultNavigationModel PreparePrintVaultNavigationModel(int selectedTabId = 0);

        List<string> GetNotifications();

        void SaveDebug(string file, string content);
    }
}
