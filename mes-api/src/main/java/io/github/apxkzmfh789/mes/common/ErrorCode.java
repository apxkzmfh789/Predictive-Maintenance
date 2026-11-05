package io.github.apxkzmfh789.mes.common;

import org.springframework.http.HttpStatus;

public enum ErrorCode {

    // 400 입력 형식 오류 (Validation)
    INVALID_INPUT(HttpStatus.BAD_REQUEST, "입력값이 올바르지 않습니다"),

    // 404 대상 없음
    EQUIPMENT_NOT_FOUND(HttpStatus.NOT_FOUND, "설비를 찾을 수 없습니다"),
    ALARM_NOT_FOUND(HttpStatus.NOT_FOUND, "경보를 찾을 수 없습니다"),

    // 409 현재 데이터와 충돌
    EQUIPMENT_CODE_DUPLICATED(HttpStatus.CONFLICT, "이미 등록된 설비 코드입니다"),
    ALARM_STATUS_CONFLICT(HttpStatus.CONFLICT, "현재 경보 상태에서는 처리할 수 없습니다"),

    // 400 적재 파일 형식 오류
    INVALID_CSV(HttpStatus.BAD_REQUEST, "예측 파일 형식이 올바르지 않습니다"),
    INVALID_METRICS(HttpStatus.BAD_REQUEST, "metrics 파일 형식이 올바르지 않습니다"),
    UNREGISTERED_EQUIPMENT(HttpStatus.BAD_REQUEST, "등록되지 않은 설비 코드가 있습니다");

    private final HttpStatus status;
    private final String message;


    ErrorCode(HttpStatus status, String message) {
        this.status = status;
        this.message = message;
    }

    public HttpStatus getStatus() {
        return status;
    }

    public String getMessage() {
        return message;
    }
}
