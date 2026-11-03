package io.github.apxkzmfh789.mes.alarm;

import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

// 설계 문서의 경보 판정 예시(임계값 0.20, 연속 2회)를 그대로 검증
class AlarmJudgeTest {

    private static final BigDecimal THRESHOLD = new BigDecimal("0.20");

    private final AlarmJudge judge = new AlarmJudge(new AlarmProperties(2, 30, null));

    @Test
    void 한_번_튄_값은_경보가_아님() {
        JudgeResult result = judge.judge(List.of(), List.of(
                        p("22:00", "0.05"),
                        p("22:01", "0.25"),   // 연속 1
                        p("22:02", "0.10")),  // 끊김
                THRESHOLD, false, null);

        assertEquals(JudgeResult.Type.NONE, result.type());
    }

    @Test
    void 통신_공백_뒤에는_연속을_처음부터_셈() {
        JudgeResult result = judge.judge(List.of(), List.of(
                        p("22:03", "0.30"),   // 연속 1
                        p("22:07", "0.31"),   // 4분 공백 → 초기화 후 1
                        p("22:08", "0.35")),  // 연속 2 → 경보
                THRESHOLD, false, null);

        assertEquals(JudgeResult.Type.CREATE, result.type());
        assertEquals(t("22:08"), result.firstDetectedTs());
        assertEquals(2, result.detectCount());
        assertEquals(new BigDecimal("0.35"), result.maxProb());
    }

    @Test
    void 열린_경보가_있으면_새로_만들지_않고_갱신() {
        JudgeResult result = judge.judge(List.of(), List.of(
                        p("22:09", "0.40"),
                        p("22:10", "0.12"),   // 미만이어도 경보는 열린 채
                        p("22:11", "0.27")),
                THRESHOLD, true, null);

        assertEquals(JudgeResult.Type.UPDATE, result.type());
        assertEquals(2, result.detectCount());
        assertEquals(t("22:11"), result.lastDetectedTs());
        assertEquals(new BigDecimal("0.40"), result.maxProb());
    }

    @Test
    void 재발생_금지_중에는_만들지_않고_끝난_뒤에_만듦() {
        JudgeResult result = judge.judge(List.of(), List.of(
                        p("22:30", "0.30"),
                        p("22:31", "0.33"),   // 연속 2지만 금지 중
                        p("22:49", "0.10"),
                        p("22:50", "0.26"),   // 금지 끝, 연속 1
                        p("22:51", "0.29")),  // 연속 2 → 경보
                THRESHOLD, false, t("22:50"));

        assertEquals(JudgeResult.Type.CREATE, result.type());
        assertEquals(t("22:51"), result.firstDetectedTs());
        assertEquals(2, result.detectCount());
    }

    @Test
    void 이전_적재의_마지막_값과_연속을_이어서_셈() {
        JudgeResult result = judge.judge(
                List.of(p("22:59", "0.30")),   // 이전 적재 마지막
                List.of(p("23:00", "0.31")),   // 이번 적재 처음
                THRESHOLD, false, null);

        assertEquals(JudgeResult.Type.CREATE, result.type());
        assertEquals(t("23:00"), result.firstDetectedTs());
        assertEquals(2, result.detectCount());
    }

    private static LocalDateTime t(String hhmm) {
        return LocalTime.parse(hhmm).atDate(LocalDate.of(2026, 10, 31));
    }

    private static ProbPoint p(String hhmm, String prob) {
        return new ProbPoint(t(hhmm), new BigDecimal(prob));
    }
}