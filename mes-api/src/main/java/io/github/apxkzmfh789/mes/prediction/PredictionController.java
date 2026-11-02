package io.github.apxkzmfh789.mes.prediction;

import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api/predictions")
public class PredictionController {

    private final PredictionImportService importService;

    public PredictionController(PredictionImportService importService) {
        this.importService = importService;
    }

    // POST /api/predictions/import (multipart/form-data)
    @PostMapping("/import")
    public ImportResult importPredictions(
            @RequestParam("predictions") MultipartFile predictions,
            @RequestParam("metrics") MultipartFile metrics,
            @RequestParam("importedBy") String importedBy,
            @RequestParam(value = "from", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime from,
            @RequestParam(value = "to", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime to) {
        return importService.importFiles(predictions, metrics, importedBy, from, to);
    }
}