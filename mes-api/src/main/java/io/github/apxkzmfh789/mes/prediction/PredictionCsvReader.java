package io.github.apxkzmfh789.mes.prediction;

import io.github.apxkzmfh789.mes.common.BusinessException;
import io.github.apxkzmfh789.mes.common.ErrorCode;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;

@Component
public class PredictionCsvReader {

    private static final String HEADER = "ts,machine_id,y,prob";
    private static final DateTimeFormatter TS_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    // CSV 파일 -> 예측 행 목록
    public List<PredictionRow> read(MultipartFile file){
        List<PredictionRow> rows = new ArrayList<>();

        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(file.getInputStream(), StandardCharsets.UTF_8))) {

            // 첫 줄은 컬럼 이름
            String header = reader.readLine();
            if (header == null || !header.trim().equals(HEADER)){
                throw  new BusinessException(ErrorCode.INVALID_CSV, "첫 줄이 " + HEADER + "가 아님");
            }

            String line;
            int lineNo = 1;
            while ((line = reader.readLine()) != null) {
                lineNo++;               // 2번째 줄 : 데이터부터 읽기
                if (line.isBlank()){
                    continue;
                }
                rows.add(parseLine(line, lineNo));
            }
        } catch (IOException e) {
            throw new BusinessException(ErrorCode.INVALID_CSV, "파일을 읽을 수 없음");
        }
        return rows;
    }

    // 한 줄: ts,machine_id,y,prob
    private PredictionRow parseLine(String line, int lineNo) {
        String[] cols = line.split(",");
        if (cols.length != 4) {
            throw new BusinessException(ErrorCode.INVALID_CSV, lineNo + "번째 줄 칸 수가 " + cols.length + "개");
        }

        try {
            // D11: UTC -> KST, 한국은 서머타임이 없어 +9시간 고정
            LocalDateTime dataTs = LocalDateTime.parse(cols[0].trim(), TS_FORMAT).plusHours(9);
            String equipmentCode = cols[1].trim();
            // cols[2]는 정답 y, 저장하지 않음
            BigDecimal prob = new BigDecimal(cols[3].trim()).setScale(6, RoundingMode.HALF_UP);

            // 0과 1사이의 확률 값인지 검사
            if (prob.compareTo(BigDecimal.ZERO) < 0 || prob.compareTo(BigDecimal.ONE) > 0) {
                throw  new BusinessException(ErrorCode.INVALID_CSV, lineNo + "번째 줄 확률이 0~1 밖: " + prob);
            }
            return new PredictionRow(equipmentCode, dataTs, prob);

        } catch (DateTimeParseException | NumberFormatException e) {
            throw new BusinessException(ErrorCode.INVALID_CSV, lineNo + "번째 줄 값 오류: " + line);
        }
    }
}
