package io.github.apxkzmfh789.mes.alarm;

import io.github.apxkzmfh789.mes.common.BusinessException;
import io.github.apxkzmfh789.mes.common.ErrorCode;
import io.github.apxkzmfh789.mes.history.HistoryMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Set;

@Service
public class AlarmService {

    private static final Set<String> STATUSES = Set.of("OPEN", "ACK", "CLOSED");

    private final AlarmMapper alarmMapper;
    private final HistoryMapper historyMapper;

    public AlarmService(AlarmMapper alarmMapper, HistoryMapper historyMapper) {
        this.alarmMapper = alarmMapper;
        this.historyMapper = historyMapper;
    }

    public List<Alarm> findAll(List<String> statuses, Integer equipmentId) {
        // 허용된 상태값만
        if (statuses != null) {
            for (String status : statuses) {
                if (!STATUSES.contains(status)) {
                    throw new BusinessException(ErrorCode.INVALID_INPUT, "status는 OPEN, ACK, CLOSED 중 하나: " + status);
                }
            }
        }
        return alarmMapper.findAll(statuses, equipmentId);
    }

    public Alarm findById(int alarmId) {
        Alarm alarm = alarmMapper.findById(alarmId);
        if (alarm == null) {
            throw new BusinessException(ErrorCode.ALARM_NOT_FOUND, alarmId);
        }
        return alarm;
    }

    // 확인: OPEN → ACK (R8, R17)
    @Transactional
    public Alarm ack(int alarmId, String ackedBy) {
        int updated = alarmMapper.ack(alarmId, ackedBy);
        if (updated == 0) {
            throw statusConflictOrNotFound(alarmId);
        }
        historyMapper.insert("ALARM", alarmId, "OPEN", "ACK", ackedBy, null);
        return findById(alarmId);
    }

    // 0건일 때 이유 구분: 경보가 없으면 404, 상태가 안 맞으면 409
    private BusinessException statusConflictOrNotFound(int alarmId) {
        Alarm alarm = findById(alarmId);   // 없으면 여기서 404
        return new BusinessException(ErrorCode.ALARM_STATUS_CONFLICT,
                "alarmId " + alarmId + ", 현재 상태 " + alarm.status());
    }
}