using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Nop.Core.Domain.BM;

namespace Nop.Data.Mapping.BM
{
    /// <summary>
    /// Represents a ExternalRequest mapping configuration
    /// </summary>
    public partial class ExternalRequestMap : NopEntityTypeConfiguration<ExternalRequest>
    {
        private string prefix = "BM_";
        #region Methods

        /// <summary>
        /// Configures the entity
        /// </summary>
        /// <param name="builder">The builder to be used to configure the entity</param>
        public override void Configure(EntityTypeBuilder<ExternalRequest> builder)
        {
            builder.ToTable(prefix + nameof(ExternalRequest));
            builder.HasKey(p => p.Id);

            base.Configure(builder);
        }

        #endregion
    }
}