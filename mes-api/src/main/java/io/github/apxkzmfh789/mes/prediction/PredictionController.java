package io.github.apxkzmfh789.mes.prediction;

import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/predictions")
public class PredictionController {

    private final PredictionImportService importService;
    private final PredictionService predictionService;

    public PredictionController(PredictionImportService importService, PredictionService predictionService) {
        this.importService = importService;
        this.predictionService = predictionService;
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

    // GET /api/predictions?equipmentId=&from=&to=
    @GetMapping
    public List<Prediction> findByRange(
            @RequestParam("equipmentId") int equipmentId,
            @RequestParam("from") @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime from,
            @RequestParam("to") @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime to) {
        return predictionService.findByRange(equipmentId, from, to);
    }
}