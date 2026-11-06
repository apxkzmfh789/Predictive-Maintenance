-- mes DB와 앱 계정 생성 (SQL Server 2025)
-- SSMS에서 sa로 한 번만 실행, 그다음 schema.sql → data.sql 순서로 실행
-- <비밀번호>를 직접 정한 값으로 바꾸고, 같은 값을 환경변수 MES_DB_PASSWORD에 설정
-- 주의: 비밀번호를 넣은 채로 커밋하지 말 것
-- 사전 조건: SQL Server 인증 허용(혼합 모드), TCP 1433 사용

CREATE DATABASE mes;
GO

CREATE LOGIN mes_app WITH PASSWORD = '<비밀번호>';
GO

USE mes;
GO

-- 앱 계정은 읽기·쓰기만 (테이블 생성·삭제는 sa로 schema.sql에서)
CREATE USER mes_app FOR LOGIN mes_app;
ALTER ROLE db_datareader ADD MEMBER mes_app;
ALTER ROLE db_datawriter ADD MEMBER mes_app;
GO
