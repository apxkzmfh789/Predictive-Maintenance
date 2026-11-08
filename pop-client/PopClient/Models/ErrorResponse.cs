namespace PopClient.Models;

// 서버 에러 응답 {"code": "...", "message": "..."}
public record ErrorResponse(string Code, string Message);