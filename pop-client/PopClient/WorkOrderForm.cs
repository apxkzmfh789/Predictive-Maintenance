using PopClient.Api;
using PopClient.Models;

namespace PopClient
{
    // 작업지시 창: 진행 중(WAITING·IN_PROGRESS) 목록과 시작·완료·취소
    public class WorkOrderForm : Form
    {
        // 작업 유형 코드 → 화면 표시용 한글
        private static readonly Dictionary<string, string> WorkTypeLabels = new()
        {
            ["INSPECTION"] = "점검",
            ["REPAIR"] = "수리",
            ["REPLACE"] = "교체"
        };

        private readonly ApiClient api;
        private readonly string worker;   // 메인 화면에서 받은 작업자 이름

        private readonly DataGridView dgvWorkOrders = new();
        private readonly Label lblStatus = new();
        private readonly FlowLayoutPanel bottomPanel = new();
        private readonly Button btnStart = new() { Text = "작업 시작", AutoSize = true };
        private readonly Button btnComplete = new() { Text = "작업 완료", AutoSize = true };
        private readonly Button btnCancelWork = new() { Text = "작업 취소", AutoSize = true };
        private readonly System.Windows.Forms.Timer refreshTimer = new() { Interval = 10000 };
        private bool loading;

        public WorkOrderForm(ApiClient api, string worker)
        {
            this.api = api;
            this.worker = worker;
            BuildLayout();
            SetupColumns();

            Load += WorkOrderForm_Load;
            FormClosed += WorkOrderForm_FormClosed;
            refreshTimer.Tick += RefreshTimer_Tick;
            dgvWorkOrders.CellFormatting += DgvWorkOrders_CellFormatting;
            dgvWorkOrders.SelectionChanged += DgvWorkOrders_SelectionChanged;
            btnStart.Click += BtnStart_Click;
            btnComplete.Click += BtnComplete_Click;
            btnCancelWork.Click += BtnCancelWork_Click;

            UpdateButtons();
            refreshTimer.Start();
        }

        // ---------- 화면 배치 ----------

        private void BuildLayout()
        {
            SuspendLayout();

            var btnRefresh = new Button { Text = "새로고침", AutoSize = true };
            btnRefresh.Click += BtnRefresh_Click;
            lblStatus.AutoSize = true;
            lblStatus.Margin = new Padding(12, 8, 3, 3);

            var topPanel = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(8) };
            topPanel.Controls.Add(btnRefresh);
            topPanel.Controls.Add(lblStatus);

            dgvWorkOrders.AllowUserToAddRows = false;
            dgvWorkOrders.AllowUserToDeleteRows = false;
            dgvWorkOrders.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;
            dgvWorkOrders.Dock = DockStyle.Fill;
            dgvWorkOrders.MultiSelect = false;
            dgvWorkOrders.ReadOnly = true;
            dgvWorkOrders.RowHeadersVisible = false;
            dgvWorkOrders.SelectionMode = DataGridViewSelectionMode.FullRowSelect;

            var btnClose = new Button
            {
                Text = "닫기",
                AutoSize = true,
                DialogResult = DialogResult.Cancel,
                Margin = new Padding(24, 3, 3, 3)
            };
            bottomPanel.Dock = DockStyle.Bottom;
            bottomPanel.AutoSize = true;
            bottomPanel.Padding = new Padding(8);
            bottomPanel.Controls.Add(btnStart);
            bottomPanel.Controls.Add(btnComplete);
            bottomPanel.Controls.Add(btnCancelWork);
            bottomPanel.Controls.Add(btnClose);

            Controls.Add(dgvWorkOrders);
            Controls.Add(bottomPanel);
            Controls.Add(topPanel);

            CancelButton = btnClose;   // Esc = 닫기
            Text = $"POP - 작업지시 (작업자: {worker})";
            ShowInTaskbar = false;
            StartPosition = FormStartPosition.CenterParent;
            AutoScaleDimensions = new SizeF(7F, 15F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(1000, 480);
            ResumeLayout(false);
            PerformLayout();
        }

        // ---------- 목록 갱신 이벤트 ----------

        private async void WorkOrderForm_Load(object? sender, EventArgs e) => await LoadWorkOrdersAsync();

        private async void BtnRefresh_Click(object? sender, EventArgs e) => await LoadWorkOrdersAsync();

        private async void RefreshTimer_Tick(object? sender, EventArgs e) => await LoadWorkOrdersAsync();

        // 창을 닫으면 타이머 정리 (코드로 만든 타이머라 직접 정리)
        private void WorkOrderForm_FormClosed(object? sender, FormClosedEventArgs e)
        {
            refreshTimer.Stop();
            refreshTimer.Dispose();
        }

        // WAITING = 노랑, IN_PROGRESS = 파랑. 작업 유형은 한글로 표시
        private void DgvWorkOrders_CellFormatting(object? sender, DataGridViewCellFormattingEventArgs e)
        {
            if (e.RowIndex < 0 || e.CellStyle == null) return;
            if (dgvWorkOrders.Rows[e.RowIndex].DataBoundItem is not WorkOrder workOrder) return;

            e.CellStyle.BackColor = workOrder.Status == "IN_PROGRESS" ? Color.LightBlue : Color.LightYellow;

            if (dgvWorkOrders.Columns[e.ColumnIndex].DataPropertyName == nameof(WorkOrder.WorkType)
                && e.Value is string code
                && WorkTypeLabels.TryGetValue(code, out var label))
            {
                e.Value = label;
                e.FormattingApplied = true;
            }
        }

        private void DgvWorkOrders_SelectionChanged(object? sender, EventArgs e) => UpdateButtons();

        // ---------- 작업 버튼 ----------

        // 시작: WAITING → IN_PROGRESS, 설비 정비 중 (R13)
        private async void BtnStart_Click(object? sender, EventArgs e)
        {
            var workOrder = SelectedWorkOrder();
            if (workOrder == null) return;

            await RunActionAsync(() => api.StartWorkOrderAsync(workOrder.WorkOrderId, worker));
        }

        // 완료: 결과 코드·조치 내용 필수, 경보 종료·설비 가동 복귀 (R11)
        private async void BtnComplete_Click(object? sender, EventArgs e)
        {
            var workOrder = SelectedWorkOrder();
            if (workOrder == null) return;

            using var dialog = new CompleteDialog($"작업 완료 - 작업지시 {workOrder.WorkOrderId} ({workOrder.EquipmentCode})");
            if (dialog.ShowDialog(this) != DialogResult.OK) return;
            var request = new WorkOrderCompleteRequest(worker, dialog.ResultCode, dialog.ActionNote);

            await RunActionAsync(async () =>
            {
                await api.CompleteWorkOrderAsync(workOrder.WorkOrderId, request);
                MessageBox.Show(
                    $"작업지시 {workOrder.WorkOrderId} 완료\n경보 {workOrder.AlarmId} 종료, {workOrder.EquipmentCode} 가동 복귀",
                    "작업 완료");
            });
        }

        // 취소: WAITING에서만, 메모는 선택 (R12)
        private async void BtnCancelWork_Click(object? sender, EventArgs e)
        {
            var workOrder = SelectedWorkOrder();
            if (workOrder == null) return;

            using var dialog = new MemoDialog("작업 취소",
                $"작업지시 {workOrder.WorkOrderId} ({workOrder.EquipmentCode})를 취소합니다.\n취소 사유를 입력하세요 (선택).",
                required: false);
            if (dialog.ShowDialog(this) != DialogResult.OK) return;
            string? memo = dialog.Memo;

            await RunActionAsync(() => api.CancelWorkOrderAsync(workOrder.WorkOrderId, worker, memo));
        }

        // 버튼 동작 공통: 처리 중 잠금, 실패하면 서버 메시지 팝업, 끝나면 목록 갱신
        private async Task RunActionAsync(Func<Task> action)
        {
            bottomPanel.Enabled = false;
            try
            {
                await action();
            }
            catch (ApiException ex)
            {
                MessageBox.Show(ex.Message, "처리 실패", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
            finally
            {
                bottomPanel.Enabled = true;
                await LoadWorkOrdersAsync();
            }
        }

        // 상태에 맞는 버튼만 켬. 최종 판단은 서버
        private void UpdateButtons()
        {
            var status = SelectedWorkOrder()?.Status;
            btnStart.Enabled = status == "WAITING";
            btnComplete.Enabled = status == "IN_PROGRESS";
            btnCancelWork.Enabled = status == "WAITING";
        }

        // ---------- 작업지시 목록 ----------

        private async Task LoadWorkOrdersAsync()
        {
            if (loading) return;
            loading = true;
            try
            {
                int? selectedId = SelectedWorkOrder()?.WorkOrderId;
                var workOrders = await api.GetActiveWorkOrdersAsync();
                dgvWorkOrders.DataSource = workOrders;
                RestoreSelection(selectedId);
                lblStatus.Text = $"진행 중 작업지시 {workOrders.Count}건 · {DateTime.Now:HH:mm:ss} 갱신";
            }
            catch (ApiException ex)
            {
                lblStatus.Text = $"갱신 실패: {ex.Message}";
            }
            finally
            {
                loading = false;
                UpdateButtons();
            }
        }

        private WorkOrder? SelectedWorkOrder() => dgvWorkOrders.CurrentRow?.DataBoundItem as WorkOrder;

        private void RestoreSelection(int? workOrderId)
        {
            if (workOrderId == null) return;
            foreach (DataGridViewRow row in dgvWorkOrders.Rows)
            {
                if (row.DataBoundItem is WorkOrder workOrder && workOrder.WorkOrderId == workOrderId)
                {
                    dgvWorkOrders.CurrentCell = row.Cells[0];
                    return;
                }
            }
        }

        // ---------- 표 열 ----------

        private void SetupColumns()
        {
            dgvWorkOrders.AutoGenerateColumns = false;
            AddColumn(nameof(WorkOrder.WorkOrderId), "작업지시", 60);
            AddColumn(nameof(WorkOrder.AlarmId), "경보", 50);
            AddColumn(nameof(WorkOrder.EquipmentCode), "설비", 70);
            AddColumn(nameof(WorkOrder.WorkType), "유형", 50);
            AddColumn(nameof(WorkOrder.Assignee), "담당자", 70);
            AddColumn(nameof(WorkOrder.Status), "상태", 90);
            AddColumn(nameof(WorkOrder.Instruction), "지시 내용", 160);
            AddColumn(nameof(WorkOrder.CreatedBy), "지시자", 70);
            AddColumn(nameof(WorkOrder.StartedAt), "시작", 90, "MM-dd HH:mm");
        }

        private void AddColumn(string property, string header, float weight, string? format = null)
        {
            var column = new DataGridViewTextBoxColumn
            {
                DataPropertyName = property,
                HeaderText = header,
                FillWeight = weight
            };
            if (format != null)
            {
                column.DefaultCellStyle.Format = format;
            }
            dgvWorkOrders.Columns.Add(column);
        }
    }
}