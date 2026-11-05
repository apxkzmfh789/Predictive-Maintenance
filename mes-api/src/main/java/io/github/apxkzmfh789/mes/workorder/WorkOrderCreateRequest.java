package io.github.apxkzmfh789.mes.workorder;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

// 작업지시 생성 요청 (R10)
public record WorkOrderCreateRequest(
        @NotBlank
        @Pattern(regexp = "INSPECTION|REPAIR|REPLACE", message = "INSPECTION, REPAIR, REPLACE 중 하나")
        String workType,

        @NotBlank @Size(max = 50) String assignee,

        @Size(max = 500) String instruction,

        @NotBlank @Size(max = 50) String createdBy
) {
}