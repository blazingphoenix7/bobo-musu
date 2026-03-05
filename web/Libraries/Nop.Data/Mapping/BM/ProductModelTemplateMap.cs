using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Nop.Core.Domain.BM;

namespace Nop.Data.Mapping.BM
{
    /// <summary>
    /// Represents a ProductModelTemplate mapping configuration
    /// </summary>
    public partial class ProductModelTemplateMap : NopEntityTypeConfiguration<ProductModelTemplate>
    {
        private string prefix = "BM_";
        #region Methods

        /// <summary>
        /// Configures the entity
        /// </summary>
        /// <param name="builder">The builder to be used to configure the entity</param>
        public override void Configure(EntityTypeBuilder<ProductModelTemplate> builder)
        {
            builder.ToTable(prefix + nameof(ProductModelTemplate));
            builder.HasKey(p => p.Id);
            
            base.Configure(builder);
        }

        #endregion
    }
}