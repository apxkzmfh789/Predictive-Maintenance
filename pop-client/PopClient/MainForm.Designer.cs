namespace PopClient
{
    partial class MainForm
    {
        private System.ComponentModel.IContainer components = null;

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form 디자이너에서 생성한 코드

        private void InitializeComponent()
        {
            components = new System.ComponentModel.Container();
            topPanel = new FlowLayoutPanel();
            lblWorker = new Label();
            txtWorker = new TextBox();
            btnRefresh = new Button();
            lblStatus = new Label();
            dgvAlarms = new DataGridView();
            bottomPanel = new FlowLayoutPanel();
            btnAck = new Button();
            btnCloseAlarm = new Button();
            btnCreateWorkOrder = new Button();
            btnWorkOrders = new Button();
            refreshTimer = new System.Windows.Forms.Timer(components);
            topPanel.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)dgvAlarms).BeginInit();
            bottomPanel.SuspendLayout();
            SuspendLayout();
            //
            // topPanel
            //
            topPanel.AutoSize = true;
            topPanel.Controls.Add(lblWorker);
            topPanel.Controls.Add(txtWorker);
            topPanel.Controls.Add(btnRefresh);
            topPanel.Controls.Add(lblStatus);
            topPanel.Dock = DockStyle.Top;
            topPanel.Name = "topPanel";
            topPanel.Padding = new Padding(8);
            //
            // lblWorker
            //
            lblWorker.AutoSize = true;
            lblWorker.Margin = new Padding(3, 8, 3, 3);
            lblWorker.Name = "lblWorker";
            lblWorker.Text = "작업자";
            //
            // txtWorker
            //
            txtWorker.Margin = new Padding(3, 4, 12, 3);
            txtWorker.Name = "txtWorker";
            txtWorker.PlaceholderText = "이름 입력";
            txtWorker.Size = new Size(120, 23);
            //
            // btnRefresh
            //
            btnRefresh.AutoSize = true;
            btnRefresh.Name = "btnRefresh";
            btnRefresh.Text = "새로고침";
            btnRefresh.UseVisualStyleBackColor = true;
            //
            // lblStatus
            //
            lblStatus.AutoSize = true;
            lblStatus.Margin = new Padding(12, 8, 3, 3);
            lblStatus.Name = "lblStatus";
            //
            // dgvAlarms
            //
            dgvAlarms.AllowUserToAddRows = false;
            dgvAlarms.AllowUserToDeleteRows = false;
            dgvAlarms.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;
            dgvAlarms.Dock = DockStyle.Fill;
            dgvAlarms.MultiSelect = false;
            dgvAlarms.Name = "dgvAlarms";
            dgvAlarms.ReadOnly = true;
            dgvAlarms.RowHeadersVisible = false;
            dgvAlarms.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
            //
            // bottomPanel
            //
            bottomPanel.AutoSize = true;
            bottomPanel.Controls.Add(btnAck);
            bottomPanel.Controls.Add(btnCloseAlarm);
            bottomPanel.Controls.Add(btnCreateWorkOrder);
            bottomPanel.Controls.Add(btnWorkOrders);
            bottomPanel.Dock = DockStyle.Bottom;
            bottomPanel.Name = "bottomPanel";
            bottomPanel.Padding = new Padding(8);
            //
            // btnAck
            //
            btnAck.AutoSize = true;
            btnAck.Name = "btnAck";
            btnAck.Text = "확인 (ACK)";
            btnAck.UseVisualStyleBackColor = true;
            //
            // btnCloseAlarm
            //
            btnCloseAlarm.AutoSize = true;
            btnCloseAlarm.Name = "btnCloseAlarm";
            btnCloseAlarm.Text = "오경보 종료";
            btnCloseAlarm.UseVisualStyleBackColor = true;
            //
            // btnCreateWorkOrder
            //
            btnCreateWorkOrder.AutoSize = true;
            btnCreateWorkOrder.Name = "btnCreateWorkOrder";
            btnCreateWorkOrder.Text = "작업지시 생성";
            btnCreateWorkOrder.UseVisualStyleBackColor = true;
            //
            // btnWorkOrders
            //
            btnWorkOrders.AutoSize = true;
            btnWorkOrders.Margin = new Padding(24, 3, 3, 3);
            btnWorkOrders.Name = "btnWorkOrders";
            btnWorkOrders.Text = "작업지시 목록";
            btnWorkOrders.UseVisualStyleBackColor = true;
            //
            // refreshTimer
            //
            refreshTimer.Interval = 10000;
            //
            // MainForm
            //
            AutoScaleDimensions = new SizeF(7F, 15F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(1000, 560);
            Controls.Add(dgvAlarms);
            Controls.Add(bottomPanel);
            Controls.Add(topPanel);
            Name = "MainForm";
            StartPosition = FormStartPosition.CenterScreen;
            Text = "POP - 설비 경보";
            topPanel.ResumeLayout(false);
            topPanel.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)dgvAlarms).EndInit();
            bottomPanel.ResumeLayout(false);
            bottomPanel.PerformLayout();
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private FlowLayoutPanel topPanel;
        private Label lblWorker;
        private TextBox txtWorker;
        private Button btnRefresh;
        private Label lblStatus;
        private DataGridView dgvAlarms;
        private FlowLayoutPanel bottomPanel;
        private Button btnAck;
        private Button btnCloseAlarm;
        private Button btnCreateWorkOrder;
        private Button btnWorkOrders;
        private System.Windows.Forms.Timer refreshTimer;
    }
}