-- 설비 기준정보 초기 데이터
-- 설비 코드 = 예측 CSV의 machine_id
-- schema.sql 실행 후 SSMS에서 sa로 실행

USE mes;
GO

INSERT INTO equipment (equipment_code, equipment_name, location)
VALUES
    ('CNC-01', N'CNC 밀링 1호기', N'가공 1라인'),
    ('CNC-02', N'CNC 밀링 2호기', N'가공 1라인'),
    ('CNC-03', N'CNC 밀링 3호기', N'가공 1라인');
GO