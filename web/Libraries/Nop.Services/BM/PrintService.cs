using Nop.Core.Data;
using Nop.Core.Domain.BM;
using Nop.Core.Domain.Customers;
using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.AspNetCore.Http;
using Nop.Core.Domain.Messages;
using Nop.Services.Customers;
using Nop.Services.Messages;
using Nop.Core;

namespace Nop.Services.BM
{
  /// <summary>
  /// Print service
  /// </summary>
  public partial class PrintService : IPrintService
  {
    #region Fields

    private readonly IRepository<Request> _requestRepository;
    private readonly IRepository<RequestHistory> _requestHistoryRepository;
    private readonly IRepository<Print> _printRepository;
    private readonly IRepository<SharedPrint> _sharedPrintRepository;
    private readonly IRepository<ExternalRequest> _externalRequestRepository;
    private readonly IRepository<ExternalRequestMessage> _externalRequestMessageRepository;
    private readonly ICustomerService _customerService;
    private readonly IQueuedEmailService _queuedEmailService;
    private readonly IRepository<EmailAccount> _emailAccountRepository;
    private readonly IRepository<PrintOrderItem> _printOrderItemRepository;
    private readonly IHttpContextAccessor _httpContextAccessor;
    private readonly IStoreContext _storeContext;


    #endregion

    #region Ctor

    public PrintService(IRepository<Request> requestRepository,
                            IRepository<RequestHistory> requestHistoryRepository,
                            IRepository<Print> printRepository,
                            IRepository<SharedPrint> sharedPrintRepository,
                            IRepository<ExternalRequest> externalRequestRepository,
                            IRepository<ExternalRequestMessage> externalRequestMessageRepository,
                            ICustomerService customerService,
                            IQueuedEmailService queuedEmailService,
                            IRepository<EmailAccount> emailAccountRepository,
                            IRepository<PrintOrderItem> printOrderItemRepository,
                            IHttpContextAccessor httpContextAccessor,
                            IStoreContext storeContext)
    {
      _requestRepository = requestRepository;
      _requestHistoryRepository = requestHistoryRepository;
      _printRepository = printRepository;
      _sharedPrintRepository = sharedPrintRepository;
      _externalRequestRepository = externalRequestRepository;
      _externalRequestMessageRepository = externalRequestMessageRepository;
      _customerService = customerService;
      _queuedEmailService = queuedEmailService;
      _emailAccountRepository = emailAccountRepository;
      _printOrderItemRepository = printOrderItemRepository;
      _httpContextAccessor = httpContextAccessor;
      _storeContext = storeContext;
    }

    #endregion

    #region Methods


    public void AddAskForPrintExternal(int customerId,
                                       string name,
                                       string phone,
                                       string email,
                                       string identifier,
                                       int externalRequestTypeId,
                                       string title,
                                       string message)
    {
      var externalRequest = _externalRequestRepository.Table.FirstOrDefault(m => m.CustomerId == customerId && m.Email == email);
      var customer = _customerService.GetCustomerByEmail(email);
      if (externalRequest != null)
      {
        externalRequest.ToCustomerid = customer?.Id;
        externalRequest.Name = name;
        externalRequest.Email = email;
        externalRequest.PhoneNumber = phone;
        externalRequest.UpdatedDate = DateTime.UtcNow;
        _externalRequestRepository.Update(externalRequest);
      }
      else
      {
        externalRequest = new ExternalRequest()
        {
          ToCustomerid = customer?.Id,
          CustomerId = customerId,
          ExternalRequestTypeId = externalRequestTypeId,
          Email = email,
          PhoneNumber = phone,
          Name = name,
          Identifier = identifier,
          CreatedDate = DateTime.UtcNow,
          UpdatedDate = DateTime.UtcNow
        };
        _externalRequestRepository.Insert(externalRequest);

      }

      //Send Request Mail
      SendAskForPrintEmail(externalRequest.Email, externalRequest.Name, message);

      var externalRequestMessage = new ExternalRequestMessage()
      {
        ExternalRequestId = externalRequest.Id,
        Title = title,
        Message = message,
        CreatedDate = DateTime.UtcNow,
        UpdatedDate = DateTime.UtcNow
      };
      _externalRequestMessageRepository.Insert(externalRequestMessage);

      if (externalRequest.ToCustomerid > 0)
      {
        AddAskForPrint(customerId, externalRequest.ToCustomerid.Value, title, message, true);
      }
    }

    public void AddAskForPrint(int customerId,
                               int toCustomerId,
                               string title,
                               string message,
                               bool isMailSent = false)
    {
      var request = new Request()
      {
        Id = 0,
        CustomerId = customerId,
        ToCustomerId = toCustomerId,
        RequestStatusId = (int)RequestStatus.Pending,
        CreatedDate = DateTime.UtcNow,
        UpdatedDate = DateTime.UtcNow
      };
      _requestRepository.Insert(request);

      var requestHistory = new RequestHistory()
      {
        RequestId = request.Id,
        Title = title,
        Message = message,
        RequestStatusId = (int)RequestStatus.Pending,
        CreatedDate = DateTime.UtcNow,
        UpdatedDate = DateTime.UtcNow
      };

      //Avoid sending mail if it's sent already.
      if (!isMailSent)
      {
        var customer = _customerService.GetCustomerById(toCustomerId);
        var customerName = _customerService.GetCustomerFullName(customer);
        SendAskForPrintEmail(customer.Email, customerName, message);
      }
      _requestHistoryRepository.Insert(requestHistory);
    }

    public List<Request> GetPendingRequests(int customerId)
    {
      var requests = (from request in _requestRepository.Table
                      join requestHistory in _requestHistoryRepository.Table on request.Id equals requestHistory.RequestId
                      where request.ToCustomerId == customerId && request.RequestStatusId == (int)RequestStatus.Pending
                      group new { request, requestHistory } by request.Id into g
                      let fg = g.FirstOrDefault()
                      let hg = g.Select(m => m.requestHistory)
                      select new Request()
                      {
                        Id = fg.request.Id,
                        CustomerId = fg.request.CustomerId,
                        ToCustomerId = fg.request.ToCustomerId,
                        RequestStatusId = fg.request.RequestStatusId,
                        CreatedDate = fg.request.CreatedDate,
                        UpdatedDate = fg.request.UpdatedDate,
                        RequestHistories = hg.ToList()
                      }).ToList();

      return requests;
    }

    public List<Print> GetPrints(int customerId)
    {
      var prints = _printRepository.Table.Where(m => m.CustomerId == customerId && !m.Deleted).ToList();
      return prints;
    }

    public void AcceptPendingRequest(int customerId,
                                     int toCustomerId,
                                     int sharedPrintId,
                                     int requestId,
                                     string title,
                                     string message)
    {

      var request = _requestRepository.GetById(requestId);
      request.UpdatedDate = DateTime.UtcNow;
      request.RequestStatusId = (int)RequestStatus.Accept;
      _requestRepository.Update(request);

      var requestHistory = new RequestHistory()
      {
        RequestId = request.Id,
        Title = title,
        Message = message,
        RequestStatusId = (int)RequestStatus.Accept,
        CreatedDate = DateTime.UtcNow,
        UpdatedDate = DateTime.UtcNow
      };
      _requestHistoryRepository.Insert(requestHistory);

      var sharedPrint = new SharedPrint()
      {
        CustomerId = customerId,
        ToCustomerId = toCustomerId,
        PrintId = sharedPrintId,
        RequestId = request.Id,
        CreatedDate = DateTime.UtcNow,
        UpdatedDate = DateTime.UtcNow
      };
      _sharedPrintRepository.Insert(sharedPrint);
    }

    public void DeleteRequest(int requestId)
    {
      var request = _requestRepository.GetById(requestId);
      request.UpdatedDate = DateTime.UtcNow;
      request.RequestStatusId = (int)RequestStatus.Delete;
      _requestRepository.Update(request);
    }

    public List<Print> GetSharedPrints(int customerId)
    {
      var sharedPrints = _sharedPrintRepository.Table.Where(m => m.ToCustomerId == customerId && !m.Print.Deleted).ToList();
      var prints = new List<Print>();
      sharedPrints.ForEach(m =>
      {
        var sharedCustomer = _customerService.GetCustomerById(m.CustomerId);
        m.Print.SharedBy = sharedCustomer?.Email;
        prints.Add(m.Print);
      });
      return prints;
    }

    public List<Request> GetAllRequests(int customerId)
    {
      var requests = (from request in _requestRepository.Table
                      join requestHistory in _requestHistoryRepository.Table on request.Id equals requestHistory.RequestId
                      where (request.ToCustomerId == customerId && request.RequestStatusId == (int)RequestStatus.Pending) ||
                            (request.CustomerId == customerId && request.RequestStatusId == (int)RequestStatus.Accept && requestHistory.RequestStatusId == (int)RequestStatus.Accept)
                      group new { request, requestHistory } by request.Id into g
                      let fg = g.FirstOrDefault()
                      let hg = g.Select(m => m.requestHistory)
                      select new Request()
                      {
                        Id = fg.request.Id,
                        CustomerId = fg.request.CustomerId,
                        ToCustomerId = fg.request.ToCustomerId,
                        RequestStatusId = fg.request.RequestStatusId,
                        CreatedDate = fg.request.CreatedDate,
                        UpdatedDate = fg.request.UpdatedDate,
                        RequestHistories = hg.ToList()
                      }).OrderByDescending(m => m.Id).ToList();

      return requests;
    }

    public void AddPrint(Print print)
    {
      _printRepository.Insert(print);
    }

    public void DeletePrint(int printId)
    {
      var print = _printRepository.GetById(printId);
      print.UpdatedDate = DateTime.UtcNow;
      print.Deleted = true;
      _printRepository.Update(print);
    }

    public void MatchCustomerInExternalRequests(Customer customer)
    {
      var externalRequests = _externalRequestRepository.Table.Where(m => m.Email == customer.Email && !m.ToCustomerid.HasValue).ToList();
      foreach (var externalRequest in externalRequests)
      {
        externalRequest.ToCustomerid = customer.Id;
        externalRequest.UpdatedDate = DateTime.UtcNow;
        _externalRequestRepository.Update(externalRequest);

        foreach (var externalRequestMessage in externalRequest.ExternalRequestMessages)
        {
          AddAskForPrint(externalRequest.CustomerId, customer.Id, externalRequestMessage.Title, externalRequestMessage.Message);
        }
      }
    }

    public PrintOrderItem GetPrintOrderItem(int id)
    {
      return _printOrderItemRepository.GetById(id);
    }

    public Request GetPendingRequestById(int id)
    {
      var data = (from request in _requestRepository.Table
                  join requestHistory in _requestHistoryRepository.Table on request.Id equals requestHistory.RequestId
                  where request.Id == id &&
                        request.RequestStatusId == (int)RequestStatus.Pending &&
                        requestHistory.RequestStatusId == (int)RequestStatus.Pending
                  group new { request, requestHistory } by request.Id into g
                  let fg = g.FirstOrDefault()
                  let hg = g.Select(m => m.requestHistory)
                  select new Request()
                  {
                    Id = fg.request.Id,
                    CustomerId = fg.request.CustomerId,
                    ToCustomerId = fg.request.ToCustomerId,
                    RequestStatusId = fg.request.RequestStatusId,
                    CreatedDate = fg.request.CreatedDate,
                    UpdatedDate = fg.request.UpdatedDate,
                    RequestHistories = hg.ToList()
                  }).FirstOrDefault();

      return data;
    }

    public Print GetPrintByRequestId(int requestId)
    {
      var sharedPrint = _sharedPrintRepository.Table.FirstOrDefault(m => m.RequestId == requestId);
      return sharedPrint?.Print;
    }

    private void SendAskForPrintEmail(string emailTo, string name, string message)
    {
      var loginUrl = $"<a href='{_httpContextAccessor.HttpContext.Request.Scheme}://{_httpContextAccessor.HttpContext.Request.Host}/login'>Bobo and Musu</a>";
      message = message.Replace("Bobo and Musu", loginUrl, StringComparison.CurrentCultureIgnoreCase);
      message = message.Replace("Bobo & Musu", loginUrl, StringComparison.CurrentCultureIgnoreCase);
      message = message.Replace("\n", "<br/><br/><br/><br/>");
      string signature = @"<div>
                              <a href=""{0}"" style=""display:block;height:50px;width:142px;background:#ff6a00; border-radius: 6px; margin-bottom: 10px; width: 292px; line-height: 50px; text-align: center; color: #000; font-family: Segoe UI;font-weight : bold;text-decoration: none;"">CHECK OUT OUR STORE</a>
                              <a href=""{1}"" style=""display:inline-block;height:50px;width:142px;background:#000 url('{3}')""></a>
                              <a href=""{2}"" style=""display:inline-block;height:50px;width:148px;background:#000 url('{3}') 148px 0px""></a>
                           </div>";

      var storeUrl = _storeContext.CurrentStore.Url;
      
      //STORE URLs
      signature = string.Format(signature,
                                storeUrl,
                                "#", //Android
                                "https://testflight.apple.com/join/YqCNcUVB", //Apple
                                System.IO.Path.Combine(storeUrl, "images/store-buttons.png"));

      var emailAccount = _emailAccountRepository.TableNoTracking.FirstOrDefault(m => m.Id == 1);
      var queuedEmail = new QueuedEmail
      {
        Priority = QueuedEmailPriority.High,
        From = emailAccount.Email,
        FromName = emailAccount.DisplayName,
        To = emailTo,
        ToName = name,
        ReplyTo = "",
        ReplyToName = "",
        CC = string.Empty,
        Bcc = "",
        Subject = "Please share your fingerprint",
        Body = $"<div>{message}</div> {signature}",
        AttachmentFilePath = "",
        AttachmentFileName = "",
        AttachedDownloadId = 0,
        CreatedOnUtc = DateTime.UtcNow,
        EmailAccountId = emailAccount.Id
      };
      _queuedEmailService.InsertQueuedEmail(queuedEmail);
    }

    #endregion
  }
}