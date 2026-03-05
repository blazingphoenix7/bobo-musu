using Microsoft.AspNetCore.Mvc;
using Nop.Core;
using Nop.Core.Domain.BM;
using Nop.Core.Domain.Customers;
using Nop.Web.Factories.BM;
using Nop.Web.Framework.Mvc;
using Nop.Web.Framework.Mvc.Filters;
using Nop.Web.Framework.Security;
using Nop.Web.Models.BM;

namespace Nop.Web.Controllers
{
    public class BMPrintController : BasePublicController
    {
        #region Fields

        private readonly IWorkContext _workContext;

        private readonly IPrintModelFactory _printModelFactory;

        #endregion

        #region Ctor

        public BMPrintController(IWorkContext workContext, 
                                IPrintModelFactory printModelFactory)
        {
            _workContext = workContext;
            _printModelFactory = printModelFactory;
        }

        #endregion

        #region Methods
        
        [HttpsRequirement(SslRequirement.Yes)]
        public IActionResult PendingRequestAccept(int requestId, int toCustomerId)
        {
            if (!_workContext.CurrentCustomer.IsRegistered())
                return Challenge();

            var acceptPendingRequest = _printModelFactory.PrepareAcceptPendingRequest(requestId, toCustomerId);
            if(acceptPendingRequest == null) return RedirectToAction("Messages");

            return View(acceptPendingRequest);
        }

        [HttpPost]
        [HttpsRequirement(SslRequirement.Yes)]
        public IActionResult PendingRequestAccept(RequestModel pendingRequestAccept)
        {
            if (!_workContext.CurrentCustomer.IsRegistered())
                return Challenge();

            _printModelFactory.AcceptPendingRequest(pendingRequestAccept);

            return RedirectToAction("Messages");
        }

        [HttpsRequirement(SslRequirement.Yes)]
        public IActionResult Messages()
        {
            if (!_workContext.CurrentCustomer.IsRegistered())
                return Challenge();

            var messages = _printModelFactory.GetMessages();
            return View(messages);
        }

        [HttpsRequirement(SslRequirement.Yes)]
        public IActionResult DeleteMessage(int requestId)
        {
            if (!_workContext.CurrentCustomer.IsRegistered())
                return Challenge();

            _printModelFactory.DeleteMessage(requestId);

            return RedirectToAction("Messages");
        }

        [HttpsRequirement(SslRequirement.Yes)]
        public IActionResult AskForPrint()
        {
            if (!_workContext.CurrentCustomer.IsRegistered())
                return Challenge();

            return View(new AskForPrintListModel());
        }

        [HttpsRequirement(SslRequirement.Yes)]
        public JsonResult AskForPrintList()
        {
            if (!_workContext.CurrentCustomer.IsRegistered())
                return new NullJsonResult();

            var askForPrints = _printModelFactory.GetAskForPrints();
            return Json(askForPrints);
        }
        
        [HttpPost]
        [HttpsRequirement(SslRequirement.Yes)]
        public IActionResult AskForPrintSave(AskForPrintModel askForPrintSave)
        {
            if (!_workContext.CurrentCustomer.IsRegistered())
                return Challenge();

            var succes = _printModelFactory.AddAskForPrint(askForPrintSave, out var message);
            if(succes)
                TempData["SuccessMessage"] = $"The request sent to '{askForPrintSave.ToCustomerName}'";
            else
                TempData["SuccessMessage"] = message;

            return RedirectToAction("AskForPrint");
        }

        [HttpPost]
        [HttpsRequirement(SslRequirement.Yes)]
        public IActionResult DeletePendingRequest(int requestId)
        {
            if (!_workContext.CurrentCustomer.IsRegistered())
                return Challenge();

            _printModelFactory.DeletePendingRequest(requestId);

            return RedirectToAction("Messages");
        }

        [HttpsRequirement(SslRequirement.Yes)]
        public IActionResult MyPrints()
        {
            if (!_workContext.CurrentCustomer.IsRegistered())
                return Challenge();

            var prints = _printModelFactory.GetPrints();
            return View(prints);
        }

        [HttpsRequirement(SslRequirement.Yes)]
        public IActionResult SharedPrints()
        {
            if (!_workContext.CurrentCustomer.IsRegistered())
                return Challenge();

            var prints = _printModelFactory.GetSharedPrints();
            return View(prints);
        }

        [HttpsRequirement(SslRequirement.Yes)]
        public IActionResult DeletePrint(int printId)
        {
            if (!_workContext.CurrentCustomer.IsRegistered())
                return Challenge();

            _printModelFactory.DeletePrint(printId);

            return RedirectToAction("MyPrints");
        }

        [HttpPost]
        public IActionResult SaveDebug(string file, string content)
        {
            _printModelFactory.SaveDebug(file, content);
            return new EmptyResult();
        }

        #endregion
    }
}