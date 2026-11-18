namespace PopClient
{
    // 메모 입력 창. 오경보 종료(필수), 작업지시 취소(선택)에서 사용
    public class MemoDialog : Form
    {
        private readonly TextBox txtMemo = new();
        private readonly bool required;

        // 입력한 메모, 비어 있으면 null
        public string? Memo => string.IsNullOrWhiteSpace(txtMemo.Text) ? null : txtMemo.Text.Trim();

        public MemoDialog(string title, string prompt, bool required)
        {
            this.required = required;
            SuspendLayout();

            var lblPrompt = new Label
            {
                Text = prompt,
                AutoSize = true,
                Dock = DockStyle.Top,
                Padding = new Padding(0, 0, 0, 6)
            };

            txtMemo.Multiline = true;
            txtMemo.MaxLength = 500;
            txtMemo.ScrollBars = ScrollBars.Vertical;
            txtMemo.Dock = DockStyle.Fill;

            var btnOk = new Button { Text = "확인", AutoSize = true };
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
            body.Controls.Add(txtMemo);
            body.Controls.Add(buttons);
            body.Controls.Add(lblPrompt);
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
            ClientSize = new Size(420, 220);
            ResumeLayout(false);
            PerformLayout();
        }

        private void BtnOk_Click(object? sender, EventArgs e)
        {
            if (required && Memo == null)
            {
                MessageBox.Show("메모를 입력하세요", Text, MessageBoxButtons.OK, MessageBoxIcon.Information);
                txtMemo.Focus();
                return;
            }
            DialogResult = DialogResult.OK;
        }
    }
}