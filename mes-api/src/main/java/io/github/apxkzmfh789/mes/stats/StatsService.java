package io.github.apxkzmfh789.mes.stats;

import io.github.apxkzmfh789.mes.common.BusinessException;
import io.github.apxkzmfh789.mes.common.ErrorCode;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

@Service
public class StatsService {

    private final StatsMapper statsMapper;

    public StatsService(StatsMapper statsMapper) {
        this.statsMapper = statsMapper;
    }

    // from·to는 날짜, 둘 다 포함 → SQL에는 from 0시 이상, to 다음 날 0시 미만으로 넘김
    public List<EquipmentStats> findEquipmentStats(LocalDate from, LocalDate to) {
        validate(from, to);
        return statsMapper.findEquipmentStats(from.atStartOfDay(), to.plusDays(1).atStartOfDay());
    }

    public List<DailyStats> findDailyStats(LocalDate from, LocalDate to) {
        validate(from, to);
        return statsMapper.findDailyStats(from.atStartOfDay(), to.plusDays(1).atStartOfDay());
    }

    private void validate(LocalDate from, LocalDate to) {
        if (from.isAfter(to)) {
            throw new BusinessException(ErrorCode.INVALID_INPUT, "from은 to보다 늦을 수 없음");
        }
    }
}