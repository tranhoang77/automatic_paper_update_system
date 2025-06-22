import os
import csv
from MilvusRAG import System
from hybridsearch import HybridSearcher
from sendemail import GmailMailer
from downloadpaper import ArxivPaperDownloader


if __name__ == "__main__":
    data_dir = '/mlcv2/WorkingSpace/Personal/quannh/Project/Project/ohmni/RAG/data/arxiv_papers'
    user_info = '/mlcv2/WorkingSpace/Personal/quannh/Project/Project/ohmni/RAG/data/user/infor.csv'
    downloader = ArxivPaperDownloader(data_dir,)
    downloader.run()
    
    # Initialize the system
    rag_system = System(collection_name="test_rag_with_milvus")
    
    # Example usage
    print("\n" + "="*60)
    print("ENHANCED PAPER RAG SYSTEM")
    print("="*60)
    
    paper_list = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.pdf')]
    if not paper_list:
        print("No PDF papers found in the specified directory.")
        exit(1)
    rag_system.process_paper(paper_list, downloader)
    print("\nAll papers processed and stored in the vector database.")
    
    #search
    css_style = """
    <style>
      body { font-family: Arial, sans-serif; line-height: 1.5; }
      .paper-container {
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 20px;
          background-color: #f9f9f9;
      }
      .paper-title { font-size: 18px; font-weight: bold; color: #333; margin-bottom: 8px; }
      .paper-novelty { font-size: 14px; font-style: italic; color: #555; margin-bottom: 8px; }
      .paper-content { font-size: 14px; color: #444; white-space: pre-wrap; }
    </style>
    """
    
    mailer = GmailMailer()
    searcher = HybridSearcher(collection_name="test_rag_with_milvus")
    with open(user_info, mode='r', encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row['Name']
            email = row['email']
            topic = row['topic']
            results = searcher.search(topic, top_k=10)

            papers_html_fragment = mailer.format_results_fragment(results)

            html_body = f"""
            <html>
            <head>
              <meta charset="UTF-8">
              {css_style}
            </head>
            <body>
              <p>Xin chào <strong>{name}</strong>!</p>
              <p>Dưới đây là tóm tắt paper liên quan đến từ khóa: <em>{topic}</em>.</p>
              {papers_html_fragment}
              <p>Trân trọng,<br>Đội ngũ Summary Paper</p>
            </body>
            </html>
            """

            # Gửi email
            success = mailer.send_email_html(
                recipient_email=email,
                subject="Thông báo paper mới",
                html_content=html_body
            )
            if not success:
                print(f"[ERROR] Gửi email cho {email} thất bại.")
 