using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Nop.Core.Domain.BM;

namespace Nop.Data.Mapping.BM
{
    /// <summary>
    /// Represents a PrintOrderItem mapping configuration
    /// </summary>
    public partial class PrintOrderItemMap : NopEntityTypeConfiguration<PrintOrderItem>
    {
        private string prefix = "BM_";
        #region Methods

        /// <summary>
        /// Configures the entity
        /// </summary>
        /// <param name="builder">The builder to be used to configure the entity</param>
        public override void Configure(EntityTypeBuilder<PrintOrderItem> builder)
        {
            builder.ToTable(prefix + nameof(PrintOrderItem));
            builder.HasKey(p => p.Id);
            /*
            builder.HasOne(p => p.Print)
                .WithMany()
                .HasForeignKey(p => p.PrintId);

            builder.HasOne(p => p.OrderItem)
                .WithMany()
                .HasForeignKey(p => p.OrderItemId);
            */
            base.Configure(builder);
        }

        #endregion
    }
}