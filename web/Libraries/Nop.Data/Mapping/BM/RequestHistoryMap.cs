using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Nop.Core.Domain.BM;

namespace Nop.Data.Mapping.BM
{
    /// <summary>
    /// Represents a RequestHistory mapping configuration
    /// </summary>
    public partial class RequestHistoryMap : NopEntityTypeConfiguration<RequestHistory>
    {
        private string prefix = "BM_";
        #region Methods

        /// <summary>
        /// Configures the entity
        /// </summary>
        /// <param name="builder">The builder to be used to configure the entity</param>
        public override void Configure(EntityTypeBuilder<RequestHistory> builder)
        {
            builder.ToTable(prefix + nameof(RequestHistory));
            builder.HasKey(request => request.Id);

            base.Configure(builder);
        }

        #endregion
    }
}