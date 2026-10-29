package io.github.apxkzmfh789.mes.equipment;
import java.time.LocalDateTime;
public record Equipment(
        Integer equipmentId,
        String equipmentCode,
        String equipmentName,
        String location,
        String status,
        Boolean active,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {
}
