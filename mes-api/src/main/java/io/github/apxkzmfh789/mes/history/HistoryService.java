package io.github.apxkzmfh789.mes.history;

import io.github.apxkzmfh789.mes.common.BusinessException;
import io.github.apxkzmfh789.mes.common.ErrorCode;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Set;

@Service
public class HistoryService {

    private static final Set<String> TARGET_TYPES = Set.of("ALARM", "WORK_ORDER", "EQUIPMENT");

    private final HistoryMapper historyMapper;

    public HistoryService(HistoryMapper historyMapper) {
        this.historyMapper = historyMapper;
    }

    public List<History> findByTarget(String targetType, Integer targetId) {
        if (!TARGET_TYPES.contains(targetType)) {
            throw new BusinessException(ErrorCode.INVALID_INPUT,
                    "targetType은 ALARM, WORK_ORDER, EQUIPMENT 중 하나: " + targetType);
        }
        return historyMapper.findByTarget(targetType, targetId);
    }
}