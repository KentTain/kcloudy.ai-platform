//! API 性能基准测试

use criterion::{criterion_group, criterion_main, Criterion, BenchmarkId};

// 示例：JSON 序列化性能测试
fn bench_json_serialization(c: &mut Criterion) {
    let data = serde_json::json!({
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "测试知识库",
        "description": "这是一个测试知识库的描述信息",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    });

    c.bench_function("json_serialize", |b| {
        b.iter(|| {
            serde_json::to_string(&data).unwrap()
        })
    });

    c.bench_function("json_parse", |b| {
        let json_str = serde_json::to_string(&data).unwrap();
        b.iter(|| {
            serde_json::from_str::<serde_json::Value>(&json_str).unwrap()
        })
    });
}

// 示例：UUID 生成性能测试
fn bench_uuid_generation(c: &mut Criterion) {
    c.bench_function("uuid_v4", |b| {
        b.iter(|| uuid::Uuid::new_v4())
    });

    c.bench_function("uuid_v7", |b| {
        b.iter(|| uuid::Uuid::now_v7())
    });
}

// 示例：字符串处理性能测试
fn bench_string_operations(c: &mut Criterion) {
    let mut group = c.benchmark_group("string_operations");

    group.bench_function("string_concat", |b| {
        b.iter(|| {
            let mut s = String::new();
            for i in 0..100 {
                s.push_str(&format!("item_{} ", i));
            }
            s
        })
    });

    group.bench_function("string_interpolate", |b| {
        b.iter(|| {
            let items: Vec<String> = (0..100).map(|i| format!("item_{} ", i)).collect();
            items.join("")
        })
    });

    group.finish();
}

criterion_group!(
    benches,
    bench_json_serialization,
    bench_uuid_generation,
    bench_string_operations,
);

criterion_main!(benches);
