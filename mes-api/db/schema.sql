-- mes 스키마 (SQL Server 2025)
-- SSMS에서 sa로 실행, 앱 계정 mes_app은 읽기·쓰기만 가능
-- 주의: 다시 실행하면 기존 테이블과 데이터를 모두 지우고 새로 만듦

USE mes;
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;  -- 필터 인덱스 생성에 필요
GO

-- 자식 테이블부터 삭제 (FK 순서)
DROP TABLE IF EXISTS status_history;
DROP TABLE IF EXISTS work_order;
DROP TABLE IF EXISTS alarm;
DROP TABLE IF EXISTS prediction;
DROP TABLE IF EXISTS import_batch;
DROP TABLE IF EXISTS equipment;
GO

-- 1. 설비
CREATE TABLE equipment (
    equipment_id    INT IDENTITY(1,1) NOT NULL,
    equipment_code  VARCHAR(20)       NOT NULL,
    equipment_name  NVARCHAR(50)      NOT NULL,
    location        NVARCHAR(50)      NULL,
    status          VARCHAR(20)       NOT NULL CONSTRAINT DF_equipment_status     DEFAULT 'RUNNING',
    is_active       BIT               NOT NULL CONSTRAINT DF_equipment_is_active  DEFAULT 1,
    created_at      DATETIME2(0)      NOT NULL CONSTRAINT DF_equipment_created_at DEFAULT SYSDATETIME(),
    updated_at      DATETIME2(0)      NOT NULL CONSTRAINT DF_equipment_updated_at DEFAULT SYSDATETIME(),

    CONSTRAINT PK_equipment        PRIMARY KEY (equipment_id),
    CONSTRAINT UQ_equipment_code   UNIQUE (equipment_code),
    CONSTRAINT CK_equipment_status CHECK (status IN ('RUNNING', 'MAINTENANCE'))
);

-- 2. 적재 이력
CREATE TABLE import_batch (
    batch_id           INT IDENTITY(1,1) NOT NULL,
    file_name          NVARCHAR(260)     NOT NULL,
    data_from          DATETIME2(0)      NULL,
    data_to            DATETIME2(0)      NULL,
    model_threshold    DECIMAL(7,6)      NOT NULL,
    applied_threshold  DECIMAL(7,6)      NOT NULL,
    rows_read          INT               NOT NULL,
    rows_inserted      INT               NOT NULL,
    rows_skipped       INT               NOT NULL,
    alarms_created     INT               NOT NULL,
    imported_by        NVARCHAR(50)      NOT NULL,
    imported_at        DATETIME2(0)      NOT NULL CONSTRAINT DF_import_batch_imported_at DEFAULT SYSDATETIME(),

    CONSTRAINT PK_import_batch PRIMARY KEY (batch_id),
    CONSTRAINT CK_import_batch_threshold CHECK (
        model_threshold BETWEEN 0 AND 1
        AND applied_threshold BETWEEN 0 AND 1
    ),
    CONSTRAINT CK_import_batch_rows CHECK (
        rows_read >= 0 AND rows_inserted >= 0 AND rows_skipped >= 0 AND alarms_created >= 0
        AND rows_inserted + rows_skipped = rows_read
    ),
    CONSTRAINT CK_import_batch_range CHECK (data_from <= data_to)
);

-- 3. 예측 결과 (설비 + 데이터 시각 복합 PK, D16)
CREATE TABLE prediction (
    equipment_id  INT           NOT NULL,
    data_ts       DATETIME2(0)  NOT NULL,
    batch_id      INT           NOT NULL,
    failure_prob  DECIMAL(7,6)  NOT NULL,

    CONSTRAINT PK_prediction           PRIMARY KEY CLUSTERED (equipment_id, data_ts),
    CONSTRAINT FK_prediction_equipment FOREIGN KEY (equipment_id) REFERENCES equipment (equipment_id),
    CONSTRAINT FK_prediction_batch     FOREIGN KEY (batch_id)     REFERENCES import_batch (batch_id),
    CONSTRAINT CK_prediction_prob      CHECK (failure_prob BETWEEN 0 AND 1)
);

-- 4. 경보
CREATE TABLE alarm (
    alarm_id           INT IDENTITY(1,1) NOT NULL,
    equipment_id       INT               NOT NULL,
    batch_id           INT               NOT NULL,
    status             VARCHAR(20)       NOT NULL CONSTRAINT DF_alarm_status     DEFAULT 'OPEN',
    first_detected_ts  DATETIME2(0)      NOT NULL,
    last_detected_ts   DATETIME2(0)      NOT NULL,
    max_prob           DECIMAL(7,6)      NOT NULL,
    detect_count       INT               NOT NULL,
    created_at         DATETIME2(0)      NOT NULL CONSTRAINT DF_alarm_created_at DEFAULT SYSDATETIME(),
    acked_at           DATETIME2(0)      NULL,
    acked_by           NVARCHAR(50)      NULL,
    closed_at          DATETIME2(0)      NULL,
    closed_by          NVARCHAR(50)      NULL,
    close_reason       VARCHAR(20)       NULL,
    close_memo         NVARCHAR(500)     NULL,
    close_data_ts      DATETIME2(0)      NULL,

    CONSTRAINT PK_alarm              PRIMARY KEY (alarm_id),
    CONSTRAINT FK_alarm_equipment    FOREIGN KEY (equipment_id) REFERENCES equipment (equipment_id),
    CONSTRAINT FK_alarm_batch        FOREIGN KEY (batch_id)     REFERENCES import_batch (batch_id),
    CONSTRAINT CK_alarm_status       CHECK (status IN ('OPEN', 'ACK', 'CLOSED')),
    CONSTRAINT CK_alarm_close_reason CHECK (close_reason IN ('RESOLVED', 'FALSE_ALARM')),
    CONSTRAINT CK_alarm_values CHECK (
        max_prob BETWEEN 0 AND 1
        AND detect_count >= 1
        AND first_detected_ts <= last_detected_ts
    ),
    -- 상태와 컬럼 일치 (D18)
    CONSTRAINT CK_alarm_state CHECK (
        (status = 'OPEN'
            AND acked_at IS NULL AND acked_by IS NULL
            AND closed_at IS NULL AND closed_by IS NULL AND close_reason IS NULL
            AND close_memo IS NULL AND close_data_ts IS NULL)
        OR (status = 'ACK'
            AND acked_at IS NOT NULL AND acked_by IS NOT NULL
            AND closed_at IS NULL AND closed_by IS NULL AND close_reason IS NULL
            AND close_memo IS NULL AND close_data_ts IS NULL)
        OR (status = 'CLOSED'
            AND acked_at IS NOT NULL AND acked_by IS NOT NULL
            AND closed_at IS NOT NULL AND closed_by IS NOT NULL AND close_reason IS NOT NULL
            AND close_data_ts IS NOT NULL)
    ),
    -- 오경보는 메모 필수 (R9)
    CONSTRAINT CK_alarm_false_alarm_memo CHECK (close_reason <> 'FALSE_ALARM' OR close_memo IS NOT NULL)
);

-- 5. 보전 작업지시
CREATE TABLE work_order (
    work_order_id  INT IDENTITY(1,1) NOT NULL,
    alarm_id       INT               NOT NULL,
    status         VARCHAR(20)       NOT NULL CONSTRAINT DF_work_order_status     DEFAULT 'WAITING',
    work_type      VARCHAR(20)       NOT NULL,
    assignee       NVARCHAR(50)      NOT NULL,
    instruction    NVARCHAR(500)     NULL,
    result_code    VARCHAR(20)       NULL,
    action_note    NVARCHAR(1000)    NULL,
    created_by     NVARCHAR(50)      NOT NULL,
    created_at     DATETIME2(0)      NOT NULL CONSTRAINT DF_work_order_created_at DEFAULT SYSDATETIME(),
    started_at     DATETIME2(0)      NULL,
    completed_at   DATETIME2(0)      NULL,
    canceled_at    DATETIME2(0)      NULL,

    CONSTRAINT PK_work_order        PRIMARY KEY (work_order_id),
    CONSTRAINT FK_work_order_alarm  FOREIGN KEY (alarm_id) REFERENCES alarm (alarm_id),
    CONSTRAINT CK_work_order_status CHECK (status IN ('WAITING', 'IN_PROGRESS', 'DONE', 'CANCELED')),
    CONSTRAINT CK_work_order_type   CHECK (work_type IN ('INSPECTION', 'REPAIR', 'REPLACE')),
    CONSTRAINT CK_work_order_result CHECK (result_code IN ('NO_ISSUE', 'ADJUSTED', 'PART_REPLACED', 'REPAIRED')),
    -- 상태와 컬럼 일치 (D18)
    CONSTRAINT CK_work_order_state CHECK (
        (status = 'WAITING'
            AND started_at IS NULL AND completed_at IS NULL AND canceled_at IS NULL)
        OR (status = 'IN_PROGRESS'
            AND started_at IS NOT NULL AND completed_at IS NULL AND canceled_at IS NULL)
        OR (status = 'DONE'
            AND started_at IS NOT NULL AND completed_at IS NOT NULL AND canceled_at IS NULL
            AND result_code IS NOT NULL AND action_note IS NOT NULL)
        OR (status = 'CANCELED'
            AND started_at IS NULL AND completed_at IS NULL AND canceled_at IS NOT NULL)
    )
);

-- 6. 상태 변경 이력 (대상 ID에 FK 없음, D15)
CREATE TABLE status_history (
    history_id   INT IDENTITY(1,1) NOT NULL,
    target_type  VARCHAR(20)       NOT NULL,
    target_id    INT               NOT NULL,
    from_status  VARCHAR(20)       NULL,
    to_status    VARCHAR(20)       NOT NULL,
    changed_by   NVARCHAR(50)      NOT NULL,
    changed_at   DATETIME2(0)      NOT NULL CONSTRAINT DF_status_history_changed_at DEFAULT SYSDATETIME(),
    memo         NVARCHAR(500)     NULL,

    CONSTRAINT PK_status_history        PRIMARY KEY (history_id),
    CONSTRAINT CK_status_history_target CHECK (target_type IN ('ALARM', 'WORK_ORDER', 'EQUIPMENT'))
);
GO

-- 인덱스
-- 설비당 열린 경보 1개 (R6, D17)
CREATE UNIQUE INDEX UX_alarm_open
    ON alarm (equipment_id)
    WHERE status IN ('OPEN', 'ACK');

CREATE INDEX IX_alarm_equipment_created ON alarm (equipment_id, created_at);
CREATE INDEX IX_alarm_created           ON alarm (created_at);

-- 경보당 진행 중 작업지시 1개 (R10, D17)
CREATE UNIQUE INDEX UX_work_order_active
    ON work_order (alarm_id)
    WHERE status IN ('WAITING', 'IN_PROGRESS');

CREATE INDEX IX_work_order_alarm ON work_order (alarm_id);

CREATE INDEX IX_history_target ON status_history (target_type, target_id, changed_at);
GO