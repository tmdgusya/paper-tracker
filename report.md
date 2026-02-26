# Daily Paper Report - 2026-02-25
**Total Papers**: 5
---
## 📊 Statistics
- **Total papers collected**: 5
- **Papers with summaries**: 4
- **Average relevance score**: 7.5/10

---
## 🏆 Top Papers

### 1. SWE-Protégé: Learning to Selectively Collaborate With an Expert Unlocks Small Language Models as Software Engineering Agents

**Authors**: Patrick Tser Jern Kon, Archana Pradeep, Ang Chen, Alexander P. Ellis, Warren Hunt, Zijian Wang, John Yang, Samuel Thompson

**Published**: 2026-02-25

**Relevance Score**: 8.5/10

**Summary**: SWE-Protégé introduces a post-training framework that enables small language models to serve as effective software engineering agents by learning to selectively collaborate with a stronger expert model. By combining supervised fine-tuning on expert-augmented trajectories with reinforcement learning that penalizes degenerate behaviors, the authors post-train a 7B parameter model to achieve 42.4% on SWE-bench Verified—a 25.4% improvement over prior SLM state of the art—while using expert assistance for only ~11% of total tokens.

**Key Points**:
- Small language models (SLMs) significantly underperform larger models on long-horizon software engineering tasks like SWE-bench due to action looping and low resolution rates
- SWE-Protégé reframes software repair as an expert-protégé collaboration where an SLM learns to selectively seek guidance from a stronger expert model while remaining the sole decision-maker
- The approach combines supervised fine-tuning on expert-augmented trajectories with agentic reinforcement learning that penalizes degenerative looping and unproductive expert calls
- A post-trained Qwen2.5-Coder-7B-Instruct achieves 42.4% Pass@1 on SWE-bench Verified, a +25.4% improvement over prior SLM state of the art
- Expert assistance is used sparsely, with approximately 4 calls per task and only 11% of total tokens coming from the expert model

[📄 View Paper](https://arxiv.org/abs/2602.22124v1) | [📥 Download PDF](https://arxiv.org/pdf/2602.22124v1)

---

### 2. GradAlign: Gradient-Aligned Data Selection for LLM Reinforcement Learning

**Authors**: Ningyuan Yang, Weihua Du, Weiwei Sun, Sean Welleck, Yiming Yang

**Published**: 2026-02-25

**Relevance Score**: 7.5/10

**Summary**: GradAlign introduces a gradient-alignment-based data selection method for reinforcement learning post-training of large language models. By leveraging a small trusted validation set to score training problems based on how well their policy gradients align with validation gradients, the method creates an adaptive curriculum that is robust to unreliable rewards, distributional imbalance, and low-utility data. Experiments demonstrate consistent improvements over heuristic baselines, highlighting the importance of directional gradient signals in non-stationary policy optimization.

**Key Points**:
- RL post-training for LLMs is highly sensitive to training data quality due to non-stationarity of policy optimization, evolving rollouts, and reward feedback dynamics
- GradAlign selects training problems by measuring alignment between their policy gradients and gradients from a small trusted validation set, creating an adaptive curriculum
- The method is evaluated across three challenging data regimes: unreliable reward signals, distribution imbalance, and low-utility training corpora
- GradAlign consistently outperforms heuristic baselines like accuracy-based filtering and manual curation across all tested regimes
- Directional gradient signals are shown to be more informative than scalar metrics for navigating non-stationary RL optimization

[📄 View Paper](https://arxiv.org/abs/2602.21492v1) | [📥 Download PDF](https://arxiv.org/pdf/2602.21492v1)

---

### 3. Recovered in Translation: Efficient Pipeline for Automated Translation of Benchmarks and Datasets

**Authors**: Hanna Yukhymenko, Anton Alexandrov, Martin Vechev

**Published**: 2026-02-25

**Relevance Score**: 7.5/10

**Summary**: This paper addresses the problem of low-quality translated benchmarks undermining multilingual LLM evaluation by presenting a fully automated translation framework that adapts test-time compute scaling strategies—specifically Universal Self-Improvement (USI) and a novel multi-round ranking method called T-RANK—to produce high-quality translations. Applied to eight Eastern and Southern European languages, the framework's outputs surpass existing translated benchmarks as measured by both reference-based metrics and LLM-as-a-judge evaluations, and both the framework and resulting benchmarks are publicly released.

**Key Points**:
- Current multilingual LLM benchmarks suffer from poor translation quality, causing semantic drift and misleading evaluation metrics
- The paper proposes a fully automated translation framework leveraging test-time compute scaling strategies (USI and a novel T-RANK multi-round ranking method) to achieve higher quality benchmark translations
- The framework is applied to translate popular benchmarks into eight Eastern and Southern European languages (Ukrainian, Bulgarian, Slovak, Romanian, Lithuanian, Estonian, Turkish, Greek)
- Evaluations using reference-based metrics and LLM-as-a-judge confirm the translations surpass existing resources in quality
- Both the framework and translated benchmarks are publicly released to support reproducible multilingual AI development

[📄 View Paper](https://arxiv.org/abs/2602.22207v1) | [📥 Download PDF](https://arxiv.org/pdf/2602.22207v1)

---

### 4. Distill and Align Decomposition for Enhanced Claim Verification

**Authors**: Jabez Magomere, Elena Kochkina, Samuel Mensah, Simerjot Kaur, Fernando Acero, Arturo Oncevay, Charese H. Smiley, Xiaomo Liu, Manuela Veloso

**Published**: 2026-02-25

**Relevance Score**: 6.5/10

**Summary**: This paper addresses the challenge of aligning claim decomposition quality with downstream verification performance by proposing a reinforcement learning framework based on Group Relative Policy Optimization (GRPO). The approach combines teacher-distilled supervised finetuning with a multi-objective reward that jointly optimizes for format compliance, verifier alignment, and decomposition quality. The resulting 8B parameter decomposer achieves state-of-the-art results (71.75% macro-F1) across six evaluation settings, outperforming both prompt-based methods and existing RL approaches while maintaining high-quality subclaim generation as confirmed by human evaluation.

**Key Points**:
- Complex claim verification benefits from decomposing claims into smaller verifiable subclaims, but existing methods fail to align decomposition quality with downstream verification performance
- The paper proposes a reinforcement learning approach using Group Relative Policy Optimization (GRPO) that jointly optimizes decomposition quality and verifier alignment
- The method combines structured sequential reasoning, supervised finetuning on teacher-distilled exemplars, and a multi-objective reward balancing format compliance, verifier alignment, and decomposition quality
- An 8B parameter decomposer achieves 71.75% macro-F1 on downstream verification, outperforming prompt-based approaches and existing RL methods by significant margins
- Human evaluation confirms the generated subclaims are high quality, demonstrating that smaller models can achieve state-of-the-art claim verification

[📄 View Paper](https://arxiv.org/abs/2602.21857v1) | [📥 Download PDF](https://arxiv.org/pdf/2602.21857v1)

---

### 5. Mitigating Structural Noise in Low-Resource S2TT: An Optimized Cascaded Nepali-English Pipeline with Punctuation Restoration

**Authors**: Tangsang Chongbang, Pranesh Pyara Shrestha, Amrit Sarki, Anku Jaiswal

**Published**: 2026-02-25

**Relevance Score**: N/A/10

[📄 View Paper](https://arxiv.org/abs/2602.21647v1) | [📥 Download PDF](https://arxiv.org/pdf/2602.21647v1)

---

---
*Report generated on 2026-02-26*
*Powered by paper-tracker*