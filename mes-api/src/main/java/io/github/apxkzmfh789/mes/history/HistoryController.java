package io.github.apxkzmfh789.mes.history;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/history")
public class HistoryController {

    private final HistoryService historyService;

    public HistoryController(HistoryService historyService) {
        this.historyService = historyService;
    }

    // GET /api/history?targetType=ALARM&targetId=2 (targetId는 선택)
    @GetMapping
    public List<History> findByTarget(
            @RequestParam("targetType") String targetType,
            @RequestParam(value = "targetId", required = false) Integer targetId) {
        return historyService.findByTarget(targetType, targetId);
    }
}