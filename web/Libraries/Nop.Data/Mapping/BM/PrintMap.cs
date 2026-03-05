using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Nop.Core.Domain.BM;

namespace Nop.Data.Mapping.BM
{
    /// <summary>
    /// Represents a print mapping configuration
    /// </summary>
    public partial class PrintMap : NopEntityTypeConfiguration<Print>
    {
        private string prefix = "BM_";
        #region Methods

        /// <summary>
        /// Configures the entity
        /// </summary>
        /// <param name="builder">The builder to be used to configure the entity</param>
        public override void Configure(EntityTypeBuilder<Print> builder)
        {
            builder.ToTable(prefix + nameof(Print));
            builder.HasKey(print => print.Id);

            builder.HasOne(print => print.Customer)
                .WithMany()
                .HasForeignKey(print => print.CustomerId);

            builder.Ignore(print => print.SharedBy);

            base.Configure(builder);
        }

        #endregion
    }
}