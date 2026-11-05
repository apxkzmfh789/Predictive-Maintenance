package io.github.apxkzmfh789.mes.alarm;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/alarms")
public class AlarmController {

    private final AlarmService alarmService;

    public AlarmController(AlarmService alarmService) {
        this.alarmService = alarmService;
    }

    // GET /api/alarms?status=OPEN&status=ACK&equipmentId=2 (조건은 전부 선택)
    @GetMapping
    public List<Alarm> findAll(
            @RequestParam(value = "status", required = false) List<String> statuses,
            @RequestParam(value = "equipmentId", required = false) Integer equipmentId) {
        return alarmService.findAll(statuses, equipmentId);
    }

    // GET /api/alarms/{alarmId}
    @GetMapping("/{alarmId}")
    public Alarm findById(@PathVariable int alarmId) {
        return alarmService.findById(alarmId);
    }
}