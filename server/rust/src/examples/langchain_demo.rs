//! LangChain Rust 示例代码
//!
//! 展示如何使用 LangChain Rust 进行 AI 编排

use langchain_rust::{
    chain::{LLMChain, LLMChainBuilder},
    llm::openai::OpenAI,
    prompt::HumanMessagePromptTemplate,
    schemas::messages::Message,
};

/// 创建简单的 LLM 链
pub async fn create_simple_chain(api_key: &str) -> Result<String, Box<dyn std::error::Error>> {
    let openai = OpenAI::builder()
        .api_key(api_key)
        .model("gpt-4o-mini")
        .build()?;

    let chain = LLMChainBuilder::new()
        .llm(openai)
        .prompt(HumanMessagePromptTemplate::new("{input}"))
        .build()?;

    let result = chain
        .run(serde_json::json!({"input": "你好，请介绍一下你自己"}))
        .await?;

    Ok(result)
}

/// RAG 流程示例
pub struct RagPipeline {
    // 可以添加 embedding 模型、向量数据库等
}

impl RagPipeline {
    /// 创建新的 RAG 流程
    pub fn new() -> Self {
        Self {}
    }

    /// 执行 RAG 查询
    pub async fn query(&self, _question: &str) -> Result<String, Box<dyn std::error::Error>> {
        // 1. 将问题转换为向量
        // 2. 在向量数据库中搜索相关文档
        // 3. 构建 prompt，包含问题和相关文档
        // 4. 调用 LLM 生成回答

        // 这里是一个简化的示例
        Ok("RAG 回答示例".to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rag_pipeline_creation() {
        let pipeline = RagPipeline::new();
        // 仅验证可以创建
        let _ = pipeline;
    }
}
