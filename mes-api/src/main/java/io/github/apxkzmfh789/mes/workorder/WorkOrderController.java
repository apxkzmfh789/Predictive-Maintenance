package io.github.apxkzmfh789.mes.workorder;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class WorkOrderController {

    private final WorkOrderService workOrderService;

    public WorkOrderController(WorkOrderService workOrderService) {
        this.workOrderService = workOrderService;
    }

    // POST /api/alarms/{alarmId}/work-orders  경보에서 작업지시 생성
    @PostMapping("/alarms/{alarmId}/work-orders")
    @ResponseStatus(HttpStatus.CREATED)
    public WorkOrder create(@PathVariable int alarmId,
                            @Valid @RequestBody WorkOrderCreateRequest request) {
        return workOrderService.create(alarmId, request);
    }
}