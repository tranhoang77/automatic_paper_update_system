from pymilvus import connections

# Thay đổi host/port nếu cần
connections.connect(alias="default", host="localhost", port="19530")

# Kiểm tra kết nối
if connections.has_connection("default"):
    print("✅ Đã kết nối tới Milvus.")
else:
    print("❌ Chưa kết nối.")