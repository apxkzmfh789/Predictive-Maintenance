package io.github.apxkzmfh789.mes.equipment;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

// 설비 등록 요청 (사용자가 정할 수 있는 값만)
public record EquipmentCreateRequest(

        @NotBlank
        @Size(max = 20)
        String equipmentCode,

        @NotBlank
        @Size
        String equipmentName,

        @Size(max = 50)
        String location
) {
}
