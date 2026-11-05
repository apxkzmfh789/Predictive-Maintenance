package io.github.apxkzmfh789.mes.alarm;

import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

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

    // PATCH /api/alarms/{alarmId}/ack  본문: {"ackedBy": "이창우"}
    @PatchMapping("/{alarmId}/ack")
    public Alarm ack(@PathVariable int alarmId,
                     @Valid @RequestBody AlarmAckRequest request) {
        return alarmService.ack(alarmId, request.ackedBy());
    }

    // PATCH /api/alarms/{alarmId}/close  본문: {"closedBy": "이창우", "memo": "..."}
    @PatchMapping("/{alarmId}/close")
    public Alarm close(@PathVariable int alarmId,
                       @Valid @RequestBody AlarmCloseRequest request) {
        return alarmService.close(alarmId, request.closedBy(), request.memo());
    }
}