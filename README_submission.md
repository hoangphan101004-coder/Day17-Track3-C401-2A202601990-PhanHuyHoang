# Lab 17 - Báo cáo nộp bài

## Phân tích benchmark

Trong bộ test này, **long-term memory quan trọng nhất** vì phục vụ 4/11 case: E02, E03, E08 và E09; toàn bộ các layer đều đạt 100%, nên không có layer nào có hit rate thấp hơn. E03 retrieve nhiều nhất với 1.529 token. E07 phải ghép long-term (`Python`) với semantic (`Idempotency-Key`); thiếu một trong hai thì fail.

Memory-enabled đạt 11/11 (100%), cao hơn no-memory 2/11 (18,2%) nhưng token reduction trung bình chỉ 14,2%, so với 81,8% của no-memory. Reduction cao không đồng nghĩa tốt: baseline gần như không retrieve gì nên rẻ nhưng mất evidence cross-session, episodic và semantic.

## Ba câu hỏi thực hành

**1. Layer quan trọng nhất trong bộ test?** Long-term, vì có nhiều case nhất và kiểm tra preference qua session (E02), open loop (E03), recency/conflict (E08), cùng user isolation (E09). Episodic lưu trajectory/reflection; semantic cung cấp tri thức dùng chung; short-term giữ mạch hội thoại hiện tại.

**2. Trade-off Zep Context Block và Redis + Qdrant?** Zep tự xây user graph, tổng hợp Context Block theo relevance, lưu provenance/validity và hỗ trợ cross-session nhanh; đổi lại phụ thuộc dịch vụ cloud, indexing bất đồng bộ, latency và chi phí. Redis + Qdrant cho quyền kiểm soát dữ liệu, TTL, schema và hạ tầng, nhưng phải tự lo extraction, conflict resolution, ranking, isolation, deletion và observability.

**3. Guardrail chống memory poisoning?** Chỉ durable-write khi user đã opt-in; validate schema/type/scope; redact PII; lưu source, timestamp, confidence và validity; yêu cầu review với preference có tác động cao; tách user graph khỏi shared semantic graph; ưu tiên fact mới đúng scope nhưng giữ provenance; heartbeat không được tự cấp quyền. Retrieval phải fail closed khi evidence yếu/xung đột, và forget phải xóa mọi user-scoped store.

## Recency và compaction

E08 chứng minh fact mới theo project scope thắng fact cũ: BLUEBIRD-42 dùng TypeScript/NestJS mà không xóa lịch sử preference Python ở scope khác. E10 chứng minh sliding compaction vẫn giữ durable constraint `REVIEW-DEADLINE-1600`, Friday 16:00 dù raw turn cũ đã bị evict; buffer giữ mọi thứ nhưng token tăng tuyến tính.

Minh chứng: `reports/benchmark.html`, `reports/comparison.md`, bốn ảnh PNG và log trong `submission/`.
