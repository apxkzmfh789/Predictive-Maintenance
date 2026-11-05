package io.github.apxkzmfh789.mes.workorder;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

// 완료 요청: 결과 코드와 조치 내용 필수 (R11)
public record WorkOrderCompleteRequest(
        @NotBlank @Size(max = 50) String changedBy,

        @NotBlank
        @Pattern(regexp = "NO_ISSUE|ADJUSTED|PART_REPLACED|REPAIRED",
                message = "NO_ISSUE, ADJUSTED, PART_REPLACED, REPAIRED 중 하나")
        String resultCode,

        @NotBlank @Size(max = 1000) String actionNote
) {
}