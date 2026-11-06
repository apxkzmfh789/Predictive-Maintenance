package io.github.apxkzmfh789.mes.common;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.FieldError;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.multipart.support.MissingServletRequestPartException;
import org.springframework.web.servlet.resource.NoResourceFoundException;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    // 업무 규칙 위반 (404, 409 등)
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> handleBusiness(BusinessException e){
        ErrorCode errorCode = e.getErrorCode();
        return ResponseEntity
                .status(errorCode.getStatus())
                .body(ErrorResponse.of(errorCode, e.getMessage()));
    }

    // 요청 값 검증 실패 (@Valid, 400)
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException e){
        FieldError fieldError = e.getBindingResult().getFieldError();
        String message = (fieldError != null)
                ? fieldError.getField() + ": " + fieldError.getDefaultMessage()
                : ErrorCode.INVALID_INPUT.getMessage();
        return ResponseEntity
                .badRequest()
                .body(ErrorResponse.of(ErrorCode.INVALID_INPUT, message));
    }

    // 요청 형식 오류 (400): 파라미터 누락·타입 불일치, JSON 깨짐, 파일 누락·크기 초과
    @ExceptionHandler({MissingServletRequestParameterException.class,
            MissingServletRequestPartException.class,
            MethodArgumentTypeMismatchException.class,
            HttpMessageNotReadableException.class,
            MaxUploadSizeExceededException.class})
    public ResponseEntity<ErrorResponse> handleBadRequest(Exception e) {
        String message = switch (e) {
            case MissingServletRequestParameterException ex -> ex.getParameterName() + ": 필수 값입니다";
            case MissingServletRequestPartException ex -> ex.getRequestPartName() + ": 파일이 필요합니다";
            case MethodArgumentTypeMismatchException ex -> ex.getName() + ": 형식이 올바르지 않습니다";
            case MaxUploadSizeExceededException ex -> "파일 크기 제한(10MB)을 넘었습니다";
            default -> "요청 본문(JSON)을 읽을 수 없습니다";
        };
        return ResponseEntity
                .badRequest()
                .body(ErrorResponse.of(ErrorCode.INVALID_INPUT, message));
    }

    // 없는 주소 404, 지원하지 않는 메서드 405 (안 잡으면 아래 500 처리기로 떨어짐)
    @ExceptionHandler({NoResourceFoundException.class, HttpRequestMethodNotSupportedException.class})
    public ResponseEntity<ErrorResponse> handleRouting(Exception e) {
        ErrorCode errorCode = (e instanceof NoResourceFoundException)
                ? ErrorCode.API_NOT_FOUND
                : ErrorCode.METHOD_NOT_ALLOWED;
        return ResponseEntity
                .status(errorCode.getStatus())
                .body(ErrorResponse.of(errorCode, errorCode.getMessage()));
    }

    // 예상 못 한 오류 500: 원인은 로그에만, 응답에는 내부 내용을 숨김
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleUnexpected(Exception e) {
        log.error("처리되지 않은 예외", e);
        return ResponseEntity
                .status(ErrorCode.INTERNAL_ERROR.getStatus())
                .body(ErrorResponse.of(ErrorCode.INTERNAL_ERROR, ErrorCode.INTERNAL_ERROR.getMessage()));
    }
}
