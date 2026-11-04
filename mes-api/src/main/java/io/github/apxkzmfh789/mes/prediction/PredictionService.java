package io.github.apxkzmfh789.mes.prediction;

import io.github.apxkzmfh789.mes.common.BusinessException;
import io.github.apxkzmfh789.mes.common.ErrorCode;
import io.github.apxkzmfh789.mes.equipment.EquipmentService;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class PredictionService {

    // 한 번에 조회할 수 있는 최대 기간
    private static final Duration MAX_RANGE = Duration.ofDays(7);

    private final PredictionMapper predictionMapper;
    private final EquipmentService equipmentService;

    public PredictionService(PredictionMapper predictionMapper, EquipmentService equipmentService) {
        this.predictionMapper = predictionMapper;
        this.equipmentService = equipmentService;
    }

    public List<Prediction> findByRange(int equipmentId, LocalDateTime from, LocalDateTime to) {
        if (!from.isBefore(to)) {
            throw new BusinessException(ErrorCode.INVALID_INPUT, "from은 to보다 앞이어야 함");
        }
        if (Duration.between(from, to).compareTo(MAX_RANGE) > 0) {
            throw new BusinessException(ErrorCode.INVALID_INPUT, "조회 기간은 7일 이내");
        }

        // 없는 설비면 404 (설비 상세 조회 재사용)
        equipmentService.findById(equipmentId);

        return predictionMapper.findByRange(equipmentId, from, to);
    }
}