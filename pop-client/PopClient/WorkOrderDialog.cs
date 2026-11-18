namespace PopClient
{
    // 작업지시 입력 창: 작업 유형, 담당자, 지시 내용
    public class WorkOrderDialog : Form
    {
        // 콤보박스 항목: 화면에는 한글, 서버에는 코드
        private record WorkTypeItem(string Code, string Label)
        {
            public override string ToString() => $"{Label} ({Code})";
        }

        private readonly ComboBox cboWorkType = new();
        private readonly TextBox txtAssignee = new();
        private readonly TextBox txtInstruction = new();

        public string WorkType => ((WorkTypeItem)cboWorkType.SelectedItem!).Code;
        public string Assignee => txtAssignee.Text.Trim();
        public string? Instruction => string.IsNullOrWhiteSpace(txtInstruction.Text) ? null : txtInstruction.Text.Trim();

        public WorkOrderDialog(string title)
        {
            SuspendLayout();

            cboWorkType.DropDownStyle = ComboBoxStyle.DropDownList;
            cboWorkType.Items.AddRange(new object[]
            {
                new WorkTypeItem("INSPECTION", "점검"),
                new WorkTypeItem("REPAIR", "수리"),
                new WorkTypeItem("REPLACE", "교체")
            });
            cboWorkType.SelectedIndex = 0;
            cboWorkType.Dock = DockStyle.Fill;

            txtAssignee.MaxLength = 50;
            txtAssignee.PlaceholderText = "정비 담당자 이름";
            txtAssignee.Dock = DockStyle.Fill;

            txtInstruction.Multiline = true;
            txtInstruction.MaxLength = 500;
            txtInstruction.ScrollBars = ScrollBars.Vertical;
            txtInstruction.PlaceholderText = "선택 입력";
            txtInstruction.Dock = DockStyle.Fill;

            var table = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 3 };
            table.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
            table.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100F));
            table.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            table.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            table.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
            table.Controls.Add(NewLabel("작업 유형"), 0, 0);
            table.Controls.Add(cboWorkType, 1, 0);
            table.Controls.Add(NewLabel("담당자"), 0, 1);
            table.Controls.Add(txtAssignee, 1, 1);
            table.Controls.Add(NewLabel("지시 내용"), 0, 2);
            table.Controls.Add(txtInstruction, 1, 2);

            var btnOk = new Button { Text = "생성", AutoSize = true };
            var btnCancel = new Button { Text = "취소", AutoSize = true, DialogResult = DialogResult.Cancel };
            btnOk.Click += BtnOk_Click;

            var buttons = new FlowLayoutPanel
            {
                Dock = DockStyle.Bottom,
                AutoSize = true,
                FlowDirection = FlowDirection.RightToLeft,
                Padding = new Padding(0, 6, 0, 0)
            };
            buttons.Controls.Add(btnCancel);
            buttons.Controls.Add(btnOk);

            var body = new Panel { Dock = DockStyle.Fill, Padding = new Padding(12) };
            body.Controls.Add(table);
            body.Controls.Add(buttons);
            Controls.Add(body);

            AcceptButton = btnOk;
            CancelButton = btnCancel;
            Text = title;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = false;
            ShowInTaskbar = false;
            StartPosition = FormStartPosition.CenterParent;
            AutoScaleDimensions = new SizeF(7F, 15F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(440, 260);
            ResumeLayout(false);
            PerformLayout();
        }

        private static Label NewLabel(string text) =>
            new() { Text = text, AutoSize = true, Anchor = AnchorStyles.Left, Margin = new Padding(3, 6, 12, 3) };

        private void BtnOk_Click(object? sender, EventArgs e)
        {
            if (Assignee.Length == 0)
            {
                MessageBox.Show("담당자를 입력하세요", Text, MessageBoxButtons.OK, MessageBoxIcon.Information);
                txtAssignee.Focus();
                return;
            }
            DialogResult = DialogResult.OK;
        }
    }
}