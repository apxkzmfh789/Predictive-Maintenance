package io.github.apxkzmfh789.mes.prediction;

import io.github.apxkzmfh789.mes.common.BusinessException;
import io.github.apxkzmfh789.mes.common.ErrorCode;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigDecimal;
import java.math.RoundingMode;

@Component
public class MetricsReader{

    private final JsonMapper jsonMapper;

    public MetricsReader(JsonMapper jsonMapper) {
        this.jsonMapper = jsonMapper;
    }

    // metrics.json >> 모델 임계값 (R1)
    public BigDecimal readThreshold(MultipartFile file) {
        try (InputStream in = file.getInputStream()){
            JsonNode threshold = jsonMapper.readTree(in).get("threshold");

            if (threshold == null || !threshold.isNumber()) {
                throw new BusinessException(ErrorCode.INVALID_METRICS, "thres 값이 없음");
            }

            BigDecimal value = threshold.decimalValue().setScale(6, RoundingMode.HALF_UP);
            if (value.compareTo(BigDecimal.ZERO) < 0 || value.compareTo(BigDecimal.ONE) > 0){
                throw new BusinessException(ErrorCode.INVALID_METRICS, "threshold가 0~1 밖: " + value);
            }
            return value;

        } catch (IOException | JacksonException e) {
            throw new BusinessException(ErrorCode.INVALID_METRICS, "JSON을 읽을 수 없음");
        }
    }
}
