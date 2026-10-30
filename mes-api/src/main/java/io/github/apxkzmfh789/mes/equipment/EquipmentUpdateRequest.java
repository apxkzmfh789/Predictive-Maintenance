package io.github.apxkzmfh789.mes.equipment;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

// 설비 수정 요청 (R14: 코드와 상태는 변경 불가라 필드 없음)
public record EquipmentUpdateRequest(
        @NotBlank
        @Size(max = 50)
        String equipmentName,

        @Size(max = 50)
        String location,

        @NotNull
        Boolean active
) {
}
