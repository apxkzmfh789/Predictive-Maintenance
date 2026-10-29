package io.github.apxkzmfh789.mes.common;

// 에러 응답 JSON
// {"code": "EQUIPMENT_NOT_FOUND", "message" : "설비를 찾을 수 없습니다: 99"}
public record ErrorResponse(
        String code,
        String message
) {

    // ErrorCode와 메시지로 응답 객체 생성
    public static ErrorResponse of(ErrorCode errorCode, String message){
        return new ErrorResponse(errorCode.name(), message);
    }
}
