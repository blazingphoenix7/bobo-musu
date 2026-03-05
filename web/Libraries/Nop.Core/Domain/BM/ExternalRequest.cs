using System;
using System.Collections.Generic;

namespace Nop.Core.Domain.BM
{
    /// <summary>
    /// Represents a ExternalRequest
    /// </summary>
    public partial class ExternalRequest : BaseEntity
    {
        private ICollection<ExternalRequestMessage> _externalRequestMessages;

        public ExternalRequest()
        {
            _externalRequestMessages = new List<ExternalRequestMessage>();
        }
       
        public int CustomerId { get; set; }

        public int? ToCustomerid { get; set; }

        public int ExternalRequestTypeId { get; set; }

        public string PhoneNumber { get; set; }

        public string Email { get; set; }

        public string Name { get; set; }

        public string Identifier { get; set; }

        public DateTime CreatedDate { get; set; }

        public DateTime? UpdatedDate { get; set; }

        #region Navigation properties

        public virtual ICollection<ExternalRequestMessage> ExternalRequestMessages
        {
            get => _externalRequestMessages ?? (_externalRequestMessages = new List<ExternalRequestMessage>());
            protected set => _externalRequestMessages = value;
        }

        #endregion
    }
}