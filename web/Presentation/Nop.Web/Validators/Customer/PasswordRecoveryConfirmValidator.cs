using FluentValidation;
using Nop.Core.Domain.Customers;
using Nop.Services.Localization;
using Nop.Web.Framework.Validators;
using Nop.Web.Models.Customer;
using System.Text.RegularExpressions;

namespace Nop.Web.Validators.Customer
{
  public partial class PasswordRecoveryConfirmValidator : BaseNopValidator<PasswordRecoveryConfirmModel>
  {
    public PasswordRecoveryConfirmValidator(ILocalizationService localizationService, CustomerSettings customerSettings)
    {
      RuleFor(x => x.NewPassword).NotEmpty().WithMessage(localizationService.GetResource("Account.PasswordRecovery.NewPassword.Required"));
      RuleFor(x => x.NewPassword).Length(customerSettings.PasswordMinLength, 999).WithMessage(string.Format(localizationService.GetResource("Account.PasswordRecovery.NewPassword.LengthValidation"), customerSettings.PasswordMinLength));
      RuleFor(x => x.NewPassword).Must(p => Regex.Match(p, @"(?=.*[0-9])").Success).WithMessage("Must have at-least 1 digit");
      RuleFor(x => x.ConfirmNewPassword).NotEmpty().WithMessage(localizationService.GetResource("Account.PasswordRecovery.ConfirmNewPassword.Required"));
      RuleFor(x => x.ConfirmNewPassword).Equal(x => x.NewPassword).WithMessage(localizationService.GetResource("Account.PasswordRecovery.NewPassword.EnteredPasswordsDoNotMatch"));
    }
  }
}