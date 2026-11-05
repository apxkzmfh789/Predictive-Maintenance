package io.github.apxkzmfh789.mes.alarm;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

// 확인 요청 본문, 확인자 이름만 (R16: 로그인 없음)
public record AlarmAckRequest(
        @NotBlank @Size(max = 50) String ackedBy
) {
}