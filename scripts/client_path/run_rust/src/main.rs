//! Client-path latency runner (ai-lib-rust AiClient → mock). GOV-007 Bench B.

use std::env;
use std::path::PathBuf;
use std::time::Instant;

use ai_lib_rust::{AiClientBuilder, Message};
use serde_json::json;

#[tokio::main]
async fn main() {
    let mock_url = env::var("MOCK_HTTP_URL").unwrap_or_else(|_| "http://127.0.0.1:4010".into());
    let mock_url = mock_url.trim_end_matches('/').to_string();
    let samples: usize = env::var("SAMPLES")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(5);

    let protocol_path = env::var("AI_LIB_RUST_PROTOCOL_PATH").unwrap_or_else(|_| {
        let root = env::var("AI_LIB_RUST_ROOT").unwrap_or_else(|_| {
            PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join("../../../../ai-lib-rust")
                .to_string_lossy()
                .into()
        });
        PathBuf::from(root)
            .join("crates/ai-lib-rust/tests/fixtures/protocols")
            .to_string_lossy()
            .into()
    });

    let client = AiClientBuilder::new()
        .protocol_path(protocol_path)
        .base_url_override(&mock_url)
        .build("openai/gpt-4o")
        .await
        .expect("build client");

    let mut latencies = Vec::with_capacity(samples);
    let mut errors = 0usize;
    for _ in 0..samples {
        let t0 = Instant::now();
        match client
            .chat()
            .messages(vec![Message::user("Hello")])
            .execute()
            .await
        {
            Ok(resp) if !resp.content.is_empty() => {}
            Ok(_) => errors += 1,
            Err(e) => {
                errors += 1;
                eprintln!("error: {e}");
            }
        }
        latencies.push(t0.elapsed().as_secs_f64() * 1000.0);
    }

    let mean = latencies.iter().sum::<f64>() / latencies.len() as f64;
    let min_v = latencies.iter().cloned().fold(f64::INFINITY, f64::min);
    let max_v = latencies.iter().cloned().fold(f64::NEG_INFINITY, f64::max);

    let out = json!({
        "harness": "client-path-mock",
        "runtime": "ai-lib-rust",
        "path": "AiClient.chat.execute",
        "mock_url": mock_url,
        "model": "openai/gpt-4o",
        "samples": samples,
        "ok": samples - errors,
        "errors": errors,
        "latency_ms": {
            "mean": (mean * 100.0).round() / 100.0,
            "min": (min_v * 100.0).round() / 100.0,
            "max": (max_v * 100.0).round() / 100.0,
        }
    });
    println!("{}", serde_json::to_string_pretty(&out).unwrap());
    if errors > 0 {
        std::process::exit(1);
    }
}
