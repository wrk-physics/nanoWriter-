# 生成模拟训练数据，不依赖网络
texts = [
    "The quick brown fox jumps over the lazy dog .",
    "Machine learning is a subset of artificial intelligence .",
    "Transformers are models that process sequential data .",
    "Training a model requires a dataset and a loss function .",
    "The weather today is sunny and bright .",
    "A journey of a thousand miles begins with a single step ."
]

# 把每个句子重复很多遍，凑足训练数据量
with open('wikitext_train.txt', 'w', encoding='utf-8') as f:
    for _ in range(1000):
        for t in texts:
            f.write(t + '\n')

with open('wikitext_valid.txt', 'w', encoding='utf-8') as f:
    for _ in range(200):
        for t in texts:
            f.write(t + '\n')

print('data preparation completed')