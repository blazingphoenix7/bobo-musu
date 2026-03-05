using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Nop.Core.Domain.BM;

namespace Nop.Data.Mapping.BM
{
    /// <summary>
    /// Represents a PrintShoppingCartItem mapping configuration
    /// </summary>
    public partial class PrintShoppingCartItemMap : NopEntityTypeConfiguration<PrintShoppingCartItem>
    {
        private string prefix = "BM_";
        #region Methods

        /// <summary>
        /// Configures the entity
        /// </summary>
        /// <param name="builder">The builder to be used to configure the entity</param>
        public override void Configure(EntityTypeBuilder<PrintShoppingCartItem> builder)
        {
            builder.ToTable(prefix + nameof(PrintShoppingCartItem));
            builder.HasKey(p => p.Id);

            builder.HasOne(p => p.Print)
                .WithMany()
                .HasForeignKey(p => p.PrintId);

            base.Configure(builder);
        }

        #endregion
    }
}