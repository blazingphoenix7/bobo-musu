using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Nop.Core.Domain.BM;

namespace Nop.Data.Mapping.BM
{
    /// <summary>
    /// Represents a Request mapping configuration
    /// </summary>
    public partial class RequestMap : NopEntityTypeConfiguration<Request>
    {
        private string prefix = "BM_";
        #region Methods

        /// <summary>
        /// Configures the entity
        /// </summary>
        /// <param name="builder">The builder to be used to configure the entity</param>
        public override void Configure(EntityTypeBuilder<Request> builder)
        {
            builder.ToTable(prefix + nameof(Request));
            builder.HasKey(request => request.Id);
            builder.Ignore(request => request.RequestHistories);

            base.Configure(builder);
        }

        #endregion
    }
}