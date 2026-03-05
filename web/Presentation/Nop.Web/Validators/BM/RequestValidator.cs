using FluentValidation;
using Nop.Services.Localization;
using Nop.Web.Framework.Validators;
using Nop.Web.Models.BM;

namespace Nop.Web.Validators.BM
{
    public partial class RequestValidator : BaseNopValidator<RequestModel>
    {
        public RequestValidator(ILocalizationService localizationService)
        {
            RuleFor(x => x.Title)
                .NotEmpty()
                .WithMessage("Required");

            RuleFor(x => x.Message)
                .NotEmpty()
                .WithMessage("Required");
            
            RuleFor(x => x.SharedPrintId)
                .NotEmpty()
                .WithMessage("Required");
        }
    }
}