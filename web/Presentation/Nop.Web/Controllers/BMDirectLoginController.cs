using Microsoft.AspNetCore.Mvc;
using Nop.Services.Authentication;
using Nop.Services.Customers;
using System;
namespace Nop.Web.Controllers
{
    public class BMDirectLoginController : BasePublicController
    {
        #region Fields

        private readonly ICustomerService _customerService;
        private readonly IAuthenticationService _authenticationService;

        #endregion

        #region Ctor

        public BMDirectLoginController(ICustomerService customerService,
                                IAuthenticationService authenticationService)
        {
            _customerService = customerService;
            _authenticationService = authenticationService;
        }

        #endregion

        #region Methods

        public IActionResult Index()
        {
            try
            {
                var returnUrl = Request.Query["returnurl"];
                var customerId = Request.Query["customerid"];
                var customer = _customerService.GetCustomerById(Convert.ToInt32(customerId));
                if(!string.IsNullOrEmpty(customer.Username))
                {
                    _authenticationService.SignOut();
                    _authenticationService.SignIn(customer, false);
                    if (returnUrl == "home")
                    {
                        return Redirect("~/");
                    }
                    return Redirect(returnUrl);
                }
                return Redirect("/login");
            }
            catch
            {
                return Redirect("/login");
            }
        }

        #endregion
    }
}