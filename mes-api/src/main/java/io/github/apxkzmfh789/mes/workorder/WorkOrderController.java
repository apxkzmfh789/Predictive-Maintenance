package io.github.apxkzmfh789.mes.workorder;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

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

    // GET /api/work-orders?status=WAITING&status=IN_PROGRESS&equipmentId=2 (조건은 전부 선택)
    @GetMapping("/work-orders")
    public List<WorkOrder> findAll(
            @RequestParam(value = "status", required = false) List<String> statuses,
            @RequestParam(value = "equipmentId", required = false) Integer equipmentId) {
        return workOrderService.findAll(statuses, equipmentId);
    }

    // PATCH /api/work-orders/{workOrderId}/start  본문: {"changedBy": "김정비"}
    @PatchMapping("/work-orders/{workOrderId}/start")
    public WorkOrder start(@PathVariable int workOrderId,
                           @Valid @RequestBody WorkOrderActionRequest request) {
        return workOrderService.start(workOrderId, request);
    }

    // PATCH /api/work-orders/{workOrderId}/complete
    // 본문: {"changedBy": "김정비", "resultCode": "ADJUSTED", "actionNote": "..."}
    @PatchMapping("/work-orders/{workOrderId}/complete")
    public WorkOrder complete(@PathVariable int workOrderId,
                              @Valid @RequestBody WorkOrderCompleteRequest request) {
        return workOrderService.complete(workOrderId, request);
    }
}