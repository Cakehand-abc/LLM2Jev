# Usage guide

[简体中文](usage_zh.md) · [Back to README](../README.md)

Complete the [installation](installation.md) first. Prepare model files before use: SGLang and Transformers use Hugging Face-compatible models; MLX uses MLX-LM or MLX-VLM models.

## Offline: Python API

All three backends use `LLM2Jev` and `JevRequest`. Import the backend you installed:

```python
from llm2jev import Choice, JevRequest, LLM2Jev, Noul, Score

request = JevRequest(
    model="/path/to/model",
    state="My parcel arrived two weeks late, and my card was charged twice.",
    # include_choice_candidates=False,  # Optional: omit the full Choice candidate list
    questions={
        "department": Choice(criteria={"shipping": "Delivery", "billing": "Billing"}),
        "severity": Score(criteria=["Low", "Medium", "High"]),
        "delivery": Noul(instructions="Is this a delivery issue?"),
    },
)
```

`include_choice_candidates` is a top-level boolean for each request, defaulting to `True`. Set it to `False` to have the default renderer omit the `All candidates:` list while retaining the current Choice candidate and its description. This supports text and multimodal inputs. Every option is still scored; Noul and Score prompts are unaffected. Each request controls its own setting.

**SGLang** (Linux/NVIDIA):

```python
from llm2jev import SGLangBackend

with SGLangBackend("/path/to/model") as backend:
    response = LLM2Jev(backend=backend).evaluate(request)
```

SGLang defaults to `submission="staged"`; you can also set it to `"all"`. Put calls inside
`if __name__ == "__main__":` when using a script because SGLang starts worker processes.

**Transformers**:

```python
from llm2jev import TransformersBackend

with TransformersBackend("/path/to/model") as backend:
    response = LLM2Jev(backend=backend).evaluate(request)
```

Transformers uses CUDA when available and otherwise uses CPU. For image models, enable
`multimodal=True` in `TransformersBackend`.

**MLX** (Apple Silicon):

```python
from llm2jev import MLXBackend

with MLXBackend("/path/to/mlx-model") as backend:
    response = LLM2Jev(backend=backend).evaluate(request)
```

For image models, use `MLXBackend(..., multimodal=True)`. See [Multimodal inputs](multimodal.md).

## Online: HTTP service

Activate the virtual environment created during installation, then run `llm2jev-serve` directly. SGLang uses its native startup arguments; select MLX or Transformers with `--backend`:

**SGLang** (Linux/NVIDIA):

```bash
llm2jev-serve --backend sglang --model-path /path/to/model --host 127.0.0.1 --port 30000
```

**Transformers**:

```bash
llm2jev-serve --backend transformers --model-path /path/to/model \
  --served-model-name local-model --host 127.0.0.1 --port 30000
```

**MLX** (Apple Silicon):

```bash
llm2jev-serve --backend mlx --model-path /path/to/mlx-model \
  --served-model-name local-model --host 127.0.0.1 --port 30000
```

All three services provide `POST /v1/systemone` and `GET /v1/models`. MLX and Transformers also provide a public `GET /health`. Set `LLM2JEV_API_KEY` to protect `/v1` endpoints, or pass `--api-key`.

The request's `model` must match `--served-model-name`; if no alias is set, it uses the model path.

### Python client

`Client` and `AsyncClient` extend the OpenAI Python SDK clients with `systemone.create()`. They are included in the package; no additional installation is needed.

```python
from llm2jev import Client, Choice

client = Client(base_url="http://localhost:30000/v1", api_key="unused")

print(client.models.list())
response = client.systemone.create(
    model="local-model",
    state="The customer package has not arrived.",
    questions={
        "department": Choice(
            instructions="Which department should handle this?",
            criteria={"shipping": "Delivery", "billing": "Billing"},
        ),
    },
    include_choice_candidates=False,
)
print(response.choices["department"].probabilities)
```

`questions` accepts `Choice`, `Score`, and `Noul` objects, JSON dictionaries containing `type`, or a mixture of both. `state` supports the same text, JSON, and multimodal content as offline requests. The result is a `JevResponse`, with typed answers, `usage`, `to_dict()`, and `json`. `include_choice_candidates` defaults to `True` and can be changed for each call.

The asynchronous interface uses the same arguments:

```python
import asyncio
from llm2jev import AsyncClient, Noul

async def main():
    client = AsyncClient(base_url="http://localhost:30000/v1", api_key="unused")

    response = await client.systemone.create(
        model="local-model",
        state="The customer package has not arrived.",
        questions={"delivery": Noul(instructions="Is this a delivery issue?")},
    )
    print(response.nouls["delivery"].noul)

asyncio.run(main())
```

A client can be reused for multiple requests. These short scripts omit explicit cleanup because the operating system reclaims connections when the process exits. In a long-running program, close a client when it is no longer needed with `client.close()` or `await client.close()` for the asynchronous client.

Set `base_url` to the llm2jev service's `/v1` URL. Use its configured API key, or a placeholder such as `"unused"` when authentication is disabled. The official OpenAI service does not provide `/systemone`.

OpenAI SDK resources, including `chat.completions`, `responses`, and `models`, remain available, along with its constructor options, context managers, and `with_options()`. The server must support each endpoint: SGLang provides its native OpenAI-compatible endpoints; the MLX and Transformers services currently provide only `/v1/systemone`, `/v1/models`, and `/health`.

`systemone.create()` accepts per-call `timeout`, `extra_headers`, and `extra_query`. Set retry options on the client or through `client.with_options(max_retries=...)`. HTTP failures and timeouts use the OpenAI SDK exceptions; invalid successful response bodies raise `openai.APIResponseValidationError`. Request inputs are validated with the existing request models before an HTTP request is sent.

### curl

The same request can be sent directly over HTTP:

```bash
curl http://localhost:30000/v1/systemone \
  -H "Content-Type: application/json" \
  -d '{
    "state": "The customer package has not arrived.",
    "model": "local-model",
    "questions": {
      "delivery": {
        "type": "noul",
        "instructions": "Is this a delivery issue?"
      }
    }
  }'
```

To omit the full Choice candidate list, send `"include_choice_candidates": false` at the top level of the HTTP request. All three backends support it without restarting the service. Omitting the field or sending `true` includes the full list. Only booleans are accepted; strings such as `"false"`, numbers, and `null` return 422. Example:

```json
{
  "model": "local-model",
  "state": "The customer package has not arrived.",
  "include_choice_candidates": false,
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which department should handle this?",
      "criteria": {"shipping": "Delivery", "billing": "Billing"}
    }
  }
}
```

SGLang and MLX support `--submission staged|all`. Transformers also accepts the option for CLI consistency, but it currently has no effect on inference.

## Choosing between staged and all

The table below gives starting points for SGLang. MLX also supports both modes, using explicit prefix prefill; Transformers currently does not apply this option.

| Request pattern | Starting point | Reason |
| --- | --- | --- |
| Long context, many candidates, no relevant cache yet | `staged` (default) | Avoids repeating shared-prefix work within a cold request |
| Short input, few candidates | `all` | Reduces the overhead of multiple submissions |
| Repeated requests with most prefixes already cached | `all` | Reuses existing cache without staged warm-up |
| Partial cache hits or highly varied inputs | Compare both | Performance depends on shared computation and submission overhead |

Backends do not detect cache state and switch modes automatically. SGLang's `staged` requires Radix Cache; use `all` when Radix Cache is disabled.
