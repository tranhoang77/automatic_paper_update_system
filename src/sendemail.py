
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class GmailMailer:
    def __init__(self, sender_email = 'tranvanhoangcs77@gmail.com', sender_password =  'dshm kcui nzyl sstj'):
        """
        Khởi tạo GmailMailer với:
        - sender_email: địa chỉ Gmail đã bật 2FA và tạo App Password.
        - sender_password: App Password 16 ký tự (không khoảng trắng).
        """
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587

    def send_email_html(self, recipient_email: str, subject: str, html_content: str) -> bool:
        """
        Gửi email với nội dung HTML:
        - recipient_email: địa chỉ người nhận.
        - subject: tiêu đề email.
        - html_content: chuỗi HTML đã wrap đủ <html>…<body>…</body></html>.
        Trả về True nếu gửi thành công, False nếu có lỗi.
        """
        msg = MIMEMultipart("alternative")
        msg["From"] = self.sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject

        mime_html = MIMEText(html_content, "html")
        msg.attach(mime_html)

        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            print(f"[INFO] Email HTML gửi thành công tới {recipient_email}")
            return True
        except Exception as e:
            print(f"[ERROR] Gửi email thất bại: {e}")
            try:
                server.quit()
            except:
                pass
            return False

    def format_results_fragment(self, results: list) -> str:
        """
        Chỉ tạo phần fragment chứa danh sách paper (không có <html> hoặc <body>).
        Mỗi phần tử results là dict theo cấu trúc:
        {
          'hit': {
            'entity': {
              'title_paper': ...,
              'novelty': ...,
              'content': ...
            }
          }
        }
        Trả về chuỗi HTML fragment.
        """
        html_parts = []

        if not results:
            html_parts.append("<p>Không tìm thấy paper nào phù hợp với từ khóa.</p>")
        else:
            for idx, item in enumerate(results, start=1):
                entity = item.get("hit", {}).get("entity", {})
                title = entity.get("title_paper", "N/A")
                novelty = entity.get("novelty", "N/A")
                content = entity.get("content", "N/A")
                pdf_url = entity.get("pdf_url", "N/A")

                paper_html = f"""
                <div class="paper-container">
                  <div class="paper-title">{idx}. {title}</div>
                  <div class="paper-novelty"><strong>Novelty:</strong> {novelty}</div>
                  <div class="paper-content"><strong>Summary:</strong><br>{content}</div>
                  <a href="{pdf_url}">Đọc bài báo trên arXiv</a>
                </div>
                """
                html_parts.append(paper_html)

        return "".join(html_parts)


