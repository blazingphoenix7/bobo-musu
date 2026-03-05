using FluentValidation;
using Nop.Core.Domain.BM;
using Nop.Services.Localization;
using Nop.Web.Framework.Validators;
using Nop.Web.Models.BM;

namespace Nop.Web.Validators.BM
{
    public partial class AskForPrintValidator : BaseNopValidator<AskForPrintModel>
    {
        public AskForPrintValidator(ILocalizationService localizationService)
        {
            RuleFor(x => x.ToCustomerName)
                .NotEmpty()
                .WithMessage("Required");

            RuleFor(x => x.Title)
                .NotEmpty()
                .WithMessage("Required");

            RuleFor(x => x.Message)
                .NotEmpty()
                .WithMessage("Required");
        }
    }
}