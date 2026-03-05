using Newtonsoft.Json;
namespace Nop.Web.Models.BM
{
    public partial class ApiResponse<T> where T : class
    {
        [JsonProperty(PropertyName = "status")]
        public int StatusCode { get; set; }

        [JsonProperty(NullValueHandling = NullValueHandling.Ignore, PropertyName = "error_message")]
        public string ErrorMessage { get; set; }

        [JsonProperty(NullValueHandling = NullValueHandling.Ignore, PropertyName = "data")]
        public T Data { get; set; }

        public ApiResponse(int statusCode,
            T data = null,
            string errorMessage = null)
        {
            StatusCode = statusCode;
            Data = data;
            ErrorMessage = errorMessage;
        }
    }

    public enum ApiStatusCode
    {
        Success = 0,
        Error = 1
    }
}
