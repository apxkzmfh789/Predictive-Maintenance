package io.github.apxkzmfh789.mes.prediction;

import io.github.apxkzmfh789.mes.alarm.AlarmProperties;
import io.github.apxkzmfh789.mes.common.BusinessException;
import io.github.apxkzmfh789.mes.common.ErrorCode;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
public class PredictionImportService {

    private final PredictionCsvReader csvReader;
    private final MetricsReader metricsReader;
    private final AlarmProperties alarmProperties;

    public PredictionImportService(PredictionCsvReader csvReader,
                                   MetricsReader metricsReader,
                                   AlarmProperties alarmProperties) {
        this.csvReader = csvReader;
        this.metricsReader = metricsReader;
        this.alarmProperties = alarmProperties;
    }

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

        // 읽은 데이터의 첫 시각, 마지막 시각
        LocalDateTime dataFrom = null;
        LocalDateTime dataTo = null;
        for (PredictionRow row : rows) {
            if (dataFrom == null || row.dataTs().isBefore(dataFrom)) {
                dataFrom = row.dataTs();
            }
            if (dataTo == null || row.dataTs().isAfter(dataTo)) {
                dataTo = row.dataTs();
            }
        }

        // 3단계: 예측 저장, 5단계: 경보 판정 추가 예정
        return new ImportResult(null, rows.size(), 0, 0, 0,
                dataFrom, dataTo, modelThreshold, appliedThreshold);
    }
}