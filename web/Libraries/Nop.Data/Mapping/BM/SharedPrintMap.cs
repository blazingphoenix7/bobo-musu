using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Nop.Core.Domain.BM;

namespace Nop.Data.Mapping.BM
{
    /// <summary>
    /// Represents a SharedPrintMap mapping configuration
    /// </summary>
    public partial class SharedPrintMap : NopEntityTypeConfiguration<SharedPrint>
    {
        private string prefix = "BM_";
        #region Methods

        /// <summary>
        /// Configures the entity
        /// </summary>
        /// <param name="builder">The builder to be used to configure the entity</param>
        public override void Configure(EntityTypeBuilder<SharedPrint> builder)
        {
            builder.ToTable(prefix + nameof(SharedPrint));
            builder.HasKey(sharePrint => sharePrint.Id);

            builder.HasOne(sharePrint => sharePrint.Print)
                .WithMany()
                .HasForeignKey(sharePrint => sharePrint.PrintId);

            base.Configure(builder);
        }

        #endregion
    }
}