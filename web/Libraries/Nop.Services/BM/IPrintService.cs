using Nop.Core.Domain.BM;
using Nop.Core.Domain.Customers;
using System.Collections.Generic;

namespace Nop.Services.BM
{
    /// <summary>
    /// Customer print interface
    /// </summary>
    public partial interface IPrintService
    {
        void AddAskForPrint(int customerId, int toCustomerId, string title, string message, bool isMailSent = false);

        void AddAskForPrintExternal(int customerId, string name, string phone, string email, string identifier, int externalRequestTypeId, string title, string message);

        List<Request> GetPendingRequests(int customerId);

        List<Print> GetPrints(int customerId);

        void AcceptPendingRequest(int customerId, int toCustomerId, int sharedPrintId, int requestId, string title, string message);

        void DeleteRequest(int requestId);

        List<Print> GetSharedPrints(int customerId);

        List<Request> GetAllRequests(int customerId);

        void AddPrint(Print print);

        void DeletePrint(int printId);

        void MatchCustomerInExternalRequests(Customer customer);

        PrintOrderItem GetPrintOrderItem(int id);

        Request GetPendingRequestById(int id);

        Print GetPrintByRequestId(int requestId);
    }
}