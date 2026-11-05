package io.github.apxkzmfh789.mes.alarm;

import io.github.apxkzmfh789.mes.common.BusinessException;
import io.github.apxkzmfh789.mes.common.ErrorCode;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Set;

@Service
public class AlarmService {

    private static final Set<String> STATUSES = Set.of("OPEN", "ACK", "CLOSED");

    private final AlarmMapper alarmMapper;

    public AlarmService(AlarmMapper alarmMapper) {
        this.alarmMapper = alarmMapper;
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
}