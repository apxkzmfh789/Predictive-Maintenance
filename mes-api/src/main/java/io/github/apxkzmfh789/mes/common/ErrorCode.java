package io.github.apxkzmfh789.mes.common;

import org.springframework.http.HttpStatus;

public enum ErrorCode {

    // 400 입력 형식 오류 (Validation)
    INVALID_INPUT(HttpStatus.BAD_REQUEST, "입력값이 올바르지 않습니다"),

    // 404 대상 없음
    EQUIPMENT_NOT_FOUND(HttpStatus.NOT_FOUND, "설비를 찾을 수 없습니다"),

    // 409 현재 데이터와 충돌
    EQUIPMENT_CODE_DUPLICATED(HttpStatus.CONFLICT, "이미 등록된 설비 코드입니다");

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
