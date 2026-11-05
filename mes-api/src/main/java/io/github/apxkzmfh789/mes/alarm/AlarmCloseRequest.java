package io.github.apxkzmfh789.mes.alarm;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

// 오경보 종료 요청, 메모 필수 (R9)
public record AlarmCloseRequest(
        @NotBlank @Size(max = 50) String closedBy,
        @NotBlank @Size(max = 500) String memo
) {
}