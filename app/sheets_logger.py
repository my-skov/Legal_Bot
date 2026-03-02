from __future__ import annotations

from datetime import datetime

import gspread

from app.retry import retry_call


class GoogleSheetsLogger:
    def __init__(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        service_account_file: str,
        max_retries: int = 4,
        retry_base_delay_seconds: float = 1.0,
    ) -> None:
        self.enabled = bool(spreadsheet_id and service_account_file)
        self._worksheet = None
        self.max_retries = max_retries
        self.retry_base_delay_seconds = retry_base_delay_seconds

        if not self.enabled:
            return

        def _open_worksheet():
            gc = gspread.service_account(filename=service_account_file)
            sheet = gc.open_by_key(spreadsheet_id)
            return sheet.worksheet(worksheet_name)

        self._worksheet = retry_call(
            _open_worksheet,
            operation_name="google_sheets_open_worksheet",
            max_attempts=self.max_retries,
            base_delay_seconds=self.retry_base_delay_seconds,
        )
        self._ensure_header()

    def _ensure_header(self) -> None:
        if self._worksheet is None:
            return
        first_row = self._worksheet.row_values(1)
        if not first_row:
            retry_call(
                lambda: self._worksheet.append_row(
                    ["timestamp", "telegram_user_id", "question", "answer"]
                ),
                operation_name="google_sheets_create_header",
                max_attempts=self.max_retries,
                base_delay_seconds=self.retry_base_delay_seconds,
            )
            return

        normalized = [item.strip().lower() for item in first_row]
        if "username" in normalized:
            username_col_idx = normalized.index("username") + 1
            retry_call(
                lambda: self._worksheet.delete_columns(username_col_idx),
                operation_name="google_sheets_drop_username_column",
                max_attempts=self.max_retries,
                base_delay_seconds=self.retry_base_delay_seconds,
            )

        retry_call(
            lambda: self._worksheet.update(
                "A1:D1",
                [["timestamp", "telegram_user_id", "question", "answer"]],
            ),
            operation_name="google_sheets_update_header",
            max_attempts=self.max_retries,
            base_delay_seconds=self.retry_base_delay_seconds,
        )

    def append_qa(
        self,
        telegram_user_id: int | None,
        question: str,
        answer: str,
    ) -> None:
        if not self.enabled or self._worksheet is None:
            return
        retry_call(
            lambda: self._worksheet.append_row(
                [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    telegram_user_id or "",
                    question,
                    answer,
                ],
                value_input_option="USER_ENTERED",
            ),
            operation_name="google_sheets_append_qa",
            max_attempts=self.max_retries,
            base_delay_seconds=self.retry_base_delay_seconds,
        )

