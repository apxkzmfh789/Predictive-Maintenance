package io.github.apxkzmfh789.mes.workorder;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

// 시작·취소 공용 요청: 처리자와 선택 메모 (R16)
public record WorkOrderActionRequest(
        @NotBlank @Size(max = 50) String changedBy,
        @Size(max = 500) String memo
) {
}