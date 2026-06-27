"""生成 V1 vs V2 RAG 评测对比图（答辩用）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from pathlib import Path

# 注册中文字体
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

OUT = Path(__file__).parent
V1 = "#9aa5b1"   # 灰
V2 = "#2f81f7"   # 蓝
UP = "#2ea043"   # 绿

# ---- 图1：核心指标分组对比 ----
groups = [
    ("长文档\nhit@1", 0.0, 87.5),
    ("长文档\nhit@3", 0.0, 100.0),
    ("长文档\nMRR", 0.0, 93.8),
    ("多轮跟进\nhit@3", 50.0, 83.3),
    ("多轮跟进\nhit@1", 50.0, 66.7),
    ("单轮FAQ\nhit@1", 100.0, 100.0),
    ("路由\n准确率", 100.0, 100.0),
]
labels = [g[0] for g in groups]
v1 = [g[1] for g in groups]
v2 = [g[2] for g in groups]
x = range(len(groups))
w = 0.38

fig, ax = plt.subplots(figsize=(13, 6.2))
b1 = ax.bar([i - w / 2 for i in x], v1, w, label="第一代 (Gen-1)", color=V1)
b2 = ax.bar([i + w / 2 for i in x], v2, w, label="第二代 (Gen-2)", color=V2)

for bars in (b1, b2):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 1.5, f"{h:.1f}",
                ha="center", va="bottom", fontsize=10, fontweight="bold")

# 提升箭头标注
for i, (lab, a, bb) in enumerate(groups):
    if bb - a > 0.1:
        ax.annotate(f"+{bb - a:.1f}pp", xy=(i, max(a, bb) + 8),
                    ha="center", color=UP, fontsize=11, fontweight="bold")

ax.set_xticks(list(x))
ax.set_xticklabels(labels, fontsize=11)
ax.set_ylabel("指标数值 (%)", fontsize=12)
ax.set_ylim(0, 120)
ax.set_title("运维数字员工 · RAG 检索能力 第一代 → 第二代 量化对比",
             fontsize=15, fontweight="bold", pad=16)
ax.legend(fontsize=12, loc="upper right")
ax.grid(axis="y", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "chart_v1_vs_v2.png", dpi=160, bbox_inches="tight")
print("saved:", OUT / "chart_v1_vs_v2.png")

# ---- 图2：多轮改写 LLM vs 规则兜底 对照 ----
metrics = ["多轮 hit@1", "多轮 hit@3"]
rule = [66.7, 83.3]
llm = [58.3, 83.3]
RULE = "#2ea043"  # 绿
LLM = "#f0883e"   # 橙
x2 = range(len(metrics))

fig2, ax2 = plt.subplots(figsize=(8, 6))
r1 = ax2.bar([i - w / 2 for i in x2], rule, w, label="规则兜底改写(确定性)", color=RULE)
r2 = ax2.bar([i + w / 2 for i in x2], llm, w, label="LLM改写(DeepSeek-R1:1.5B)", color=LLM)
for bars in (r1, r2):
    for b in bars:
        h = b.get_height()
        ax2.text(b.get_x() + b.get_width() / 2, h + 1, f"{h:.1f}",
                 ha="center", va="bottom", fontsize=12, fontweight="bold")
ax2.set_xticks(list(x2))
ax2.set_xticklabels(metrics, fontsize=12)
ax2.set_ylabel("命中率 (%)", fontsize=12)
ax2.set_ylim(0, 100)
ax2.set_title("多轮改写对照：本地1.5B小模型下\n确定性规则反而优于LLM自由改写",
              fontsize=13, fontweight="bold", pad=14)
ax2.legend(fontsize=11, loc="upper left")
ax2.grid(axis="y", alpha=0.3)
ax2.spines[["top", "right"]].set_visible(False)
ax2.annotate("规则 +8.4pp", xy=(0, 70), ha="center", color=RULE,
             fontsize=12, fontweight="bold")
fig2.tight_layout()
fig2.savefig(OUT / "chart_rewrite_compare.png", dpi=160, bbox_inches="tight")
print("saved:", OUT / "chart_rewrite_compare.png")
