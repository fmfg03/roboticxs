use openhuman_embed::{Access, AgentDefinitionSpec, AgentSpec, Provider, Runtime, SandboxModeSpec, ToolScopeSpec, Workspace};
use serde_json::json;
use wiremock::{Mock, MockServer, ResponseTemplate};
use wiremock::matchers::{method, path};

#[test]
fn public_embed_agent_is_rejected_before_the_stub_provider() {
    std::thread::Builder::new()
        .stack_size(16 * 1024 * 1024)
        .spawn(|| {
            tokio::runtime::Builder::new_multi_thread()
                .enable_all()
                .thread_stack_size(16 * 1024 * 1024)
                .build()
                .unwrap()
                .block_on(async { tokio::spawn(repro()).await.unwrap() });
        })
        .unwrap()
        .join()
        .unwrap();
}

async fn repro() {
        let provider = MockServer::start().await;
        Mock::given(method("POST")).and(path("/v1/chat/completions")).respond_with(ResponseTemplate::new(200).set_body_json(json!({"id":"x","object":"chat.completion","created":1,"model":"stub","choices":[{"index":0,"message":{"role":"assistant","content":"pong"},"finish_reason":"stop"}],"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2}}))).mount(&provider).await;
        let workspace = tempfile::tempdir().unwrap();
        let connected = std::env::var("REPRO_CONNECTED").is_ok();
        let readonly = std::env::var("REPRO_READONLY").is_ok();
        let runtime = if connected {
            openhuman_tinyhumans::RuntimeBuilder::new()
                .workspace(Workspace::dir(workspace.path()))
                .backend_url(provider.uri())
                .api_key("test")
                .build().await.unwrap()
        } else {
            Runtime::builder().workspace(Workspace::dir(workspace.path())).build().await.unwrap()
        };
        let access = if readonly { Access::readonly() } else { Access::full() };
        let agent = runtime.agent(AgentSpec::new("repro").provider(Provider::openai_compatible(format!("{}/v1", provider.uri()), "test").model("stub")).access(access).definition(AgentDefinitionSpec::new().tools(ToolScopeSpec::Named(vec![])).sandbox(SandboxModeSpec::ReadOnly))).unwrap();
        let error = agent.turn("say pong").send().await.unwrap_err();
        assert!(error.to_string().contains("hosted agent invocation was rejected by policy"));
        assert_eq!(provider.received_requests().await.unwrap().len(), 0);
}
