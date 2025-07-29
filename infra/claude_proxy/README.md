# LionAGI Claude Code Proxy

to use please first install `lionagi` and `fastapi`

```bash
uv add lionagi fastapi loguru
```

then run the proxy with:

```bash
uv run cookbooks/claude_proxy/claude_code_proxy.py --port 8000
```

Next, configure a cutsom endpoint 

```python
from lionagi.service import Endpoint, EndpointConfig, iModel
claude_code_config = EndpointConfig(
    name="claude_code_cli_proxy",
    provider="claude_code_proxy",
    base_url="http://localhost:8000/v1",
    endpoint="query",
    api_key="dummy_api_key",
    kwargs={"model": "sonnet"},
)
cc_proxy_endpoint = Endpoint(claude_code_config)
claude_code = iModel(endpoint=cc_proxy_endpoint)
```

Done, now you can run `claude code` in jupyter or any other environment that supports `lionagi`.
