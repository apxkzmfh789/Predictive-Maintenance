namespace PopClient.Api;

// 서버가 에러를 돌려줬거나 연결 자체가 안 될 때. 화면은 이것만 잡으면 됨
public class ApiException : Exception
{
    public int StatusCode { get; }   // 404, 409 등. 연결 실패는 0
    public string Code { get; }      // ALARM_STATUS_CONFLICT 등

    public ApiException(int statusCode, string code, string message) : base(message)
    {
        StatusCode = statusCode;
        Code = code;
    }
}