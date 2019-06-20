# Installation

```
git clone https://github.com/numberoverzero/scaffolding.git
pip install -e scaffolding
```

# CLI

Generate and run a stubbed service:

```
scaffold generate-resources \
  --spec ~/my-spec.yaml \
  --out out.py
python out.py
```

Generate bloop-based Dynamodb models:

```
scaffold generate-models \
  --backend dynamodb-bloop \
  --spec ~/my-proto-spec.yaml \
  --out models.py
```
