package io.github.apxkzmfh789.mes.prediction;

import io.github.apxkzmfh789.mes.alarm.AlarmDetectionService;
import io.github.apxkzmfh789.mes.alarm.AlarmProperties;
import io.github.apxkzmfh789.mes.alarm.ProbPoint;
import io.github.apxkzmfh789.mes.common.BusinessException;
import io.github.apxkzmfh789.mes.common.ErrorCode;
import io.github.apxkzmfh789.mes.equipment.Equipment;
import io.github.apxkzmfh789.mes.equipment.EquipmentMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;

@Service
public class PredictionImportService {

    private final PredictionCsvReader csvReader;
    private final MetricsReader metricsReader;
    private final AlarmProperties alarmProperties;
    private final EquipmentMapper equipmentMapper;
    private final ImportBatchMapper importBatchMapper;
    private final PredictionMapper predictionMapper;
    private final AlarmDetectionService alarmDetectionService;

    public PredictionImportService(PredictionCsvReader csvReader,
                                   MetricsReader metricsReader,
                                   AlarmProperties alarmProperties,
                                   EquipmentMapper equipmentMapper,
                                   ImportBatchMapper importBatchMapper,
                                   PredictionMapper predictionMapper, AlarmDetectionService alarmDetectionService) {
        this.csvReader = csvReader;
        this.metricsReader = metricsReader;
        this.alarmProperties = alarmProperties;
        this.equipmentMapper = equipmentMapper;
        this.importBatchMapper = importBatchMapper;
        this.predictionMapper = predictionMapper;
        this.alarmDetectionService = alarmDetectionService;
    }

    @Transactional
    public ImportResult importFiles(MultipartFile predictionsFile, MultipartFile metricsFile,
                                    String importedBy, LocalDateTime from, LocalDateTime to) {
        if (importedBy == null || importedBy.isBlank()) {
            throw new BusinessException(ErrorCode.INVALID_INPUT, "importedBy가 비어 있음");
        }
        if (from != null && to != null && !from.isBefore(to)) {
            throw new BusinessException(ErrorCode.INVALID_INPUT, "from은 to보다 앞이어야 함");
        }

        // R1: 재정의 값이 있으면 그 값, 없으면 metrics.json
        BigDecimal modelThreshold = metricsReader.readThreshold(metricsFile);
        BigDecimal appliedThreshold = (alarmProperties.thresholdOverride() != null)
                ? alarmProperties.thresholdOverride()
                : modelThreshold;

        // D20: from 이상, to 미만만 남김 (KST 데이터 시각)
        List<PredictionRow> rows = new ArrayList<>();
        for (PredictionRow row : csvReader.read(predictionsFile)) {
            if (from != null && row.dataTs().isBefore(from)) {
                continue;
            }
            if (to != null && !row.dataTs().isBefore(to)) {
                continue;
            }
            rows.add(row);
        }

        // 설비 코드 → 설비 (equipment 전체를 한 번만 조회)
        Map<String, Equipment> equipmentByCode = new HashMap<>();
        for (Equipment equipment : equipmentMapper.findAll()) {
            equipmentByCode.put(equipment.equipmentCode(), equipment);
        }

        // R3, D21: 등록 안 된 코드가 하나라도 있으면 전체 거부
        TreeSet<String> unknownCodes = new TreeSet<>();
        for (PredictionRow row : rows) {
            if (!equipmentByCode.containsKey(row.equipmentCode())) {
                unknownCodes.add(row.equipmentCode());
            }
        }
        if (!unknownCodes.isEmpty()) {
            throw new BusinessException(ErrorCode.UNREGISTERED_EQUIPMENT, unknownCodes);
        }

        // 적재 이력 먼저 생성 (예측의 FK)
        int batchId = importBatchMapper.insert(
                predictionsFile.getOriginalFilename(), modelThreshold, appliedThreshold, importedBy);

        int inserted = 0;
        int skipped = 0;
        LocalDateTime dataFrom = null;
        LocalDateTime dataTo = null;
        Map<Integer, List<ProbPoint>> newPointsByEquipment = new HashMap<>();

        for (PredictionRow row : rows) {
            if (dataFrom == null || row.dataTs().isBefore(dataFrom)) {
                dataFrom = row.dataTs();
            }
            if (dataTo == null || row.dataTs().isAfter(dataTo)) {
                dataTo = row.dataTs();
            }

            Equipment equipment = equipmentByCode.get(row.equipmentCode());

            // R3: 사용하지 않는 설비는 건너뜀
            if (!equipment.active()) {
                skipped++;
                continue;
            }

            // R2: 이미 있는 (설비, 시각)이면 0
            int result = predictionMapper.insertIfAbsent(
                    equipment.equipmentId(), row.dataTs(), batchId, row.failureProb());
            if (result == 1) {
                inserted++;
                // 경보 판정용으로 설비별로 모음
                List<ProbPoint> points = newPointsByEquipment.get(equipment.equipmentId());
                if (points == null) {
                    points = new ArrayList<>();
                    newPointsByEquipment.put(equipment.equipmentId(), points);
                }
                points.add(new ProbPoint(row.dataTs(), row.failureProb()));
            } else {
                skipped++;
            }
        }

        // 경보 판정 (R4: 새로 저장된 예측만)
        int alarmsCreated = alarmDetectionService.detect(newPointsByEquipment, appliedThreshold, batchId);

        ImportResult result = new ImportResult(batchId, rows.size(), inserted, skipped, alarmsCreated,
                dataFrom, dataTo, modelThreshold, appliedThreshold);
        importBatchMapper.updateResult(result);
        return result;
    }
}