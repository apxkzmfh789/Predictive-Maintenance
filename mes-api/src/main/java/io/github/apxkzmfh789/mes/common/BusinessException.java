package io.github.apxkzmfh789.mes.common;

public class BusinessException extends RuntimeException {

    private final ErrorCode errorCode;

    // ErrorCode의 기본 메시지 사용
    public BusinessException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.errorCode = errorCode;
    }

    // 기본 메시지 뒤에 상세값 추가 (예: "설비를 찾을 수 없습니다: 99")
    public BusinessException(ErrorCode errorCode, Object detail) {
        super(errorCode.getMessage() + ": " + detail);
        this.errorCode = errorCode;
    }

    public ErrorCode getErrorCode() {
        return errorCode;
    }
}
