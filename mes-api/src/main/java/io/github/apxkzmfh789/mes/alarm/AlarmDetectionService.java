package io.github.apxkzmfh789.mes.alarm;

import io.github.apxkzmfh789.mes.history.HistoryMapper;
import io.github.apxkzmfh789.mes.prediction.PredictionMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

@Service
public class AlarmDetectionService {

    private final AlarmJudge alarmJudge;
    private final AlarmMapper alarmMapper;
    private final PredictionMapper predictionMapper;
    private final HistoryMapper historyMapper;
    private final AlarmProperties properties;

    public AlarmDetectionService(AlarmJudge alarmJudge, AlarmMapper alarmMapper,
                                 PredictionMapper predictionMapper, HistoryMapper historyMapper,
                                 AlarmProperties properties) {
        this.alarmJudge = alarmJudge;
        this.alarmMapper = alarmMapper;
        this.predictionMapper = predictionMapper;
        this.historyMapper = historyMapper;
        this.properties = properties;
    }

    // 새로 저장된 예측(설비 ID → 점 목록)으로 경보 판정, 새로 생긴 경보 수 반환
    @Transactional
    public int detect(Map<Integer, List<ProbPoint>> newPointsByEquipment,
                      BigDecimal threshold, int batchId) {
        int created = 0;

        for (Map.Entry<Integer, List<ProbPoint>> entry : newPointsByEquipment.entrySet()) {
            int equipmentId = entry.getKey();
            List<ProbPoint> newPoints = entry.getValue();
            newPoints.sort(Comparator.comparing(ProbPoint::dataTs));   // 시간순 보장

            // 직전 예측: 최신순으로 받아서 시간순으로 뒤집기
            List<ProbPoint> history = new ArrayList<>(predictionMapper.findRecentBefore(
                    equipmentId, newPoints.get(0).dataTs(), properties.consecutiveCount() - 1));
            Collections.reverse(history);

            // R6: 열린 경보, R7: 재발생 금지 끝
            Integer openAlarmId = alarmMapper.findOpenAlarmId(equipmentId);
            LocalDateTime lastCloseDataTs = alarmMapper.findLastCloseDataTs(equipmentId);
            LocalDateTime cooldownUntil = (lastCloseDataTs != null)
                    ? lastCloseDataTs.plusMinutes(properties.cooldownMinutes())
                    : null;

            JudgeResult result = alarmJudge.judge(
                    history, newPoints, threshold, openAlarmId != null, cooldownUntil);

            switch (result.type()) {
                case CREATE -> {
                    int alarmId = alarmMapper.insert(equipmentId, batchId, result);
                    historyMapper.insert("ALARM", alarmId, null, "OPEN", "SYSTEM", null);
                    created++;
                }
                case UPDATE -> alarmMapper.updateDetection(openAlarmId, result);
                case NONE -> { }
            }
        }
        return created;
    }
}