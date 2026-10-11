# JevBench 公开题目测评

[English](../en/jevbench.md) · [返回 README](../../README_zh.md)

本次测评覆盖 `original`、`easy`、`hard` 数据集中的 231 个公开题目。TypeSafe adapter 将各个决策请求发送到本地 LLM2Jev 接口。运行命令保存逐题 JSONL 结果、原始响应和测评记录；汇总命令统计准确率、校准和延时。

运行测评：

```bash
python -m jevbench.cli run \
  --tasks datasets/public/original.jsonl,datasets/public/easy.jsonl,datasets/public/hard.jsonl \
  --adapter typesafe \
  --endpoint http://127.0.0.1:30000 \
  --key-env '' \
  --model qwen3.5-4b \
  --cost-basis no_billable_account_public_endpoint \
  --reserve-usd 0 \
  --delay-s 0.2 \
  --results /data/LLM2Jev/RUN2/qwen3.5-4b-v1.jsonl \
  --raw-dir /data/LLM2Jev/RUN2/raw \
  --ledger RUN/ledger.json
```

汇总结果：

```bash
python -m jevbench.cli summarize \
  --tasks datasets/public/original.jsonl,datasets/public/easy.jsonl,datasets/public/hard.jsonl \
  --public-export /data/LLM2Jev/RUN2/qwen3.5-4b-v1-summary.json \
  --results /data/LLM2Jev/RUN2/qwen3.5-4b-v1.jsonl
```

下表使用相同公开题目比较准确率。延时以秒计；Jev 数据来自 JevBench 公布的串行测评，LLM2Jev 数据来自本地服务，部署条件不同。

| 系统 | 准确率 | 延时 P50（秒） | 延时 P95（秒） |
| --- | ---: | ---: | ---: |
| Jev 1.13.0 (TypeSafe AI) | 85.1% | 0.652 | 0.722 |
| LLM2Jev (Qwen3.5-4B) | 76.2% | 0.048 | 0.346 |
| jev-local (Qwen3.5-9B) | 74.9% | - | - |
| kev 8B (research preview) | 71.4% | - | - |
| kev 4B (research preview) | 66.2% | - | - |
| Open-Jev 2B (Zefan Cai) | 64.5% | - | - |
| jeff (Logan Markewich, GLiFormer 400M) | 62.8% | - | - |
| smalljev semantic-v9 | 60.6% | - | - |
| Laya (Convai Innovations, ModernBERT-large 421M) | 58.4% | - | - |
