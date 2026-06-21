# Deep Reinforcement Learning for EVRPTW 文献精读报告

论文：Bo Lin, Bissan Ghaddar, Jatin Nathwani. *Deep Reinforcement Learning for the Electric Vehicle Routing Problem With Time Windows*. IEEE Transactions on Intelligent Transportation Systems, 2022.

说明：本报告基于用户提供的 PDF 内容整理。PDF 中 Table I/II 的主体数值因复杂排版未能可靠抽取，因此实验部分只引用论文正文中明确可读的数字和结论，不补造表格细节。

## 0. 摘要翻译与整体定位

### a) 摘要翻译

过去十年，电动汽车快速普及，越来越多物流和运输企业开始使用电动汽车提供服务。为了建模商业电动车队运营，本文采用带时间窗的电动汽车路径问题 EVRPTW。本文提出一个端到端深度强化学习框架来求解 EVRPTW。具体而言，作者开发了一个结合 pointer network 和 graph embedding layer 的 attention model，用于参数化求解 EVRPTW 的随机策略。模型使用带 rollout baseline 的 policy gradient 训练。数值实验表明，该模型能够高效求解现有方法难以处理的大规模 EVRPTW 实例。

### b) 论文研究的问题

论文研究如何用深度强化学习直接构造 EVRPTW 的车辆路径。EV 需要服务带需求和时间窗的客户，必要时访问充电站，并最终回到 depot。目标是在满足需求、时间窗、电量和车辆数量等约束的同时最小化总行驶距离。

### c) 方法类型

本文属于强化学习方法，也可视为深度学习、强化学习和图嵌入结合的神经组合优化方法。

### d) 与 EVRP-TW 科研方向的相关度

相关度：高。它的主题正是 Deep RL for EVRP-TW，包含状态设计、动作解码、奖励函数、mask 约束处理、充电站访问和时间窗处理，是该方向必须精读的核心参考文献。

## 1. 研究动机

### a) 作者为什么提出这个方法

EVRPTW 是 NP-hard 问题。传统精确算法和元启发式在规模变大时效率下降，而且常依赖特定问题结构，不容易迁移到 EVRPTW 变体。作者希望用 RL 学到一种可快速生成可行解的策略，以支持大规模、近实时 EV 调度。

### b) 现有方法痛点

- 精确算法如 branch-price-and-cut 在大规模实例上计算代价高。
- VNS/TS 等启发式质量较好，但运行时间随规模增长明显。
- 监督学习需要高质量标签，而组合优化问题的最优标签很昂贵。
- 传统方法对新约束、新目标和动态变化的适配成本高。

### c) 核心假设或研究直觉

EVRPTW 可以被看作一个序列决策问题：每一步选择下一个访问节点。只要用图嵌入表示局部和全局信息，再用 attention policy 解码，RL 可以学到类似启发式规则的路径构造策略。

### d) 主要解决的 EVRP-TW 子问题

本文主要解决路径规划、时间窗约束、电池约束、充电决策、车辆容量和车辆数量控制。其中最核心的是在时间窗和电量约束下构造多车路径。

## 2. 方法设计：重点精读

### a) 完整方法流程

输入 EVRPTW 图实例；构造节点特征和全局车辆状态；graph embedding 融合节点、边和全局信息；LSTM decoder 记录已走路径；attention 计算下一个节点概率；mask 去除不可行动作；采样、贪心或 beam search 解码路径；用 reward 评价整条路径；最后用 REINFORCE 和 rollout baseline 更新模型。

### b) 输入信息

每个节点 `i` 的局部特征为 `X_i^t = (x_i, z_i, e_i, l_i, d_i^t)`，分别表示坐标、时间窗开始、时间窗结束和剩余需求。节点类型包括 customer、charging station 和 depot。站点和 depot 的时间窗设为 `[0,T]`，需求为 0。图是完全图，边权是欧氏距离或旅行时间。全局变量为 `G^t = {tau^t, b^t, ev^t}`，分别表示当前时间、当前 EV 电量和剩余可用 EV 数量。车辆载重没有作为神经网络输入，但在 mask 中被跟踪。

### c) 强化学习定义

- State：当前图状态 `X^t`、全局状态 `G^t` 和历史路径 `Y^t`。
- Action：选择下一个访问节点 `y_{t+1}`，即把一个 customer、station 或 depot 加到路径序列末尾。
- Reward：负总距离加约束惩罚。距离越短奖励越高；超出车辆数、访问充电站过多、电量为负都会被惩罚。
- Policy：`P(y_{t+1}=i | X^t, G^t, Y^t)`，由 attention model 输出。
- Value function：没有单独学习 critic 或 value network；作者使用 rollout baseline 降低 policy gradient 方差。
- RL 算法：REINFORCE policy gradient + rollout baseline。
- 训练过程：每步随机生成 batch 实例，随机策略采样路径，计算 reward，用 baseline 修正梯度，Adam 更新参数。论文训练 10000 iterations，约 90 小时。

### d) 模型结构

Graph embedding：先用 1D convolution 把节点特征和全局变量嵌入到 128 维，再用 Structure2Vec 聚合邻居节点、边权和全局状态，使每个节点表示同时包含局部信息和图级信息。

Attention mechanism：先计算 context vector，表示当前整张图和历史状态，再对每个节点打分，softmax 得到访问概率。

LSTM decoder：输入当前所在节点表示，维护历史路径记忆 `h_t`，帮助策略知道已经走过什么。

Masking scheme：把不合法节点的打分设成极小值，使其概率近似为 0。

Decoding：测试时比较 greedy decoding、stochastic sampling 和 beam search。stochastic sampling 每个实例采样 100 个解，取距离最短者。

### e) 公式通俗解释

状态转移公式更新当前时间、电量、可用车辆数和客户剩余需求。若从客户离开，时间加服务时间和旅行时间；若从充电站离开，先充满电再行驶；若从 depot 离开，表示开启新车路线。电量公式表示行驶消耗电量，若刚访问过站点或 depot，则相当于满电出发。奖励公式的第一项是负总距离，后面是对车辆数超限、充电站访问次数和负电量的惩罚。梯度公式是 REINFORCE：好于 baseline 的路径会提高其动作概率，差于 baseline 的路径会降低其动作概率。

### f) 约束处理

- 时间窗：若最早到达客户 `j` 已超过 `l_j`，mask 掉该客户。
- 电池：若当前电量不足以从当前节点到客户再回 depot，mask 掉该动作。
- 充电站：允许重复访问；访问后假设充满电，充电时间线性。
- 车辆容量：若客户需求已为 0 或超过当前 EV 剩余载重，mask 掉该客户。
- 车辆数量：超出车辆数主要通过 reward 惩罚。
- 路径可行性：mask 和 reward 共同处理，但作者明确承认没有理论保证一定不违反所有约束。

### g) 5 步速记版 pipeline

1. 把 EVRPTW 表示成带客户、充电站和 depot 的完全图。
2. 用节点特征和全局 EV 状态构造 RL state。
3. 用 Structure2Vec、attention 和 LSTM 输出下一个节点概率。
4. 用 mask 排除违反时间窗、电量和容量的动作。
5. 用 REINFORCE + rollout baseline 训练，测试时用采样、beam 或贪心解码路径。

## 3. 与其他方法对比

### a) 与传统优化方法相比

MIP/CPLEX 追求精确或有界解，但大规模慢；VNS/TS 依赖人工设计邻域和规则，质量强但运行时间随规模增长明显。本文方法训练成本高，但测试时一次前向解码很快，更适合大规模和动态重规划。

### b) 与主流深度学习/强化学习方法相比

相对 Nazari 的 VRP RL 框架，本文重新定义 EVRPTW 的 state、reward 和 mask，并加入 graph embedding 来捕捉全局图结构。相对普通 pointer network，它显式处理动态需求、电量、时间和充电站重复访问。

### c) 创新点判断

- 真创新：把 graph embedding + pointer/attention policy 系统适配到 EVRPTW。
- 工程组合：Structure2Vec、LSTM decoder、attention、REINFORCE 和 rollout baseline 都来自已有工作。
- 实验贡献：展示 RL 在大规模 EVRPTW 上的速度和可扩展性优势。

### d) 方法对比表

| 方法类型 | 核心思想 | 优点 | 缺点 | 是否适合 EVRP-TW | 原因 |
|---|---|---|---|---|---|
| MIP/CPLEX | 精确建模求解 | 小规模质量高 | 大规模慢 | 中 | 可做 benchmark |
| VNS/TS | 人工邻域搜索 | 解质量强 | 调参和运行耗时 | 高 | EVRPTW 经典强基线 |
| OR-Tools | 工程化约束搜索 | 易用、可扩展 | EV 电量和充电需定制 | 高 | 适合复现 baseline |
| Pointer/RL | 序列解码路径 | 端到端、快 | 约束难保证 | 中高 | 需要强化 mask |
| 本文方法 | 图嵌入 + attention RL | 速度快、规模大 | 充电决策短视 | 高 | 正对 EVRPTW |

## 4. 实验设计与结果分析

### a) 实验设置

作者比较 CPLEX、Schneider et al. 的 VNS/TS，以及本文 RL 的三种解码方式：greedy、stochastic sampling 和 beam search。

### b) 数据集

实验使用作者随机生成的仿真实例，而不是标准 Schneider benchmark。坐标在 `[0,1] x [0,1]` 均匀分布；需求从 `{0.05, 0.10, 0.15, 0.20}` 采样；时间窗按 Solomon 风格生成；训练用 10 customers、3 stations、3 EVs；测试规模变化。

### c) 评价指标

评价指标包括平均总行驶距离、相对最优或最好方法的 gap、平均求解时间、15 分钟内是否可解、2 小时内可解实例数。

### d) Baseline 公平性

CPLEX 和 VNS/TS 是合理 baseline，但实验数据为随机生成，且没有与更现代的 hybrid DRL + local search、ALNS、OR-Tools routing 等方法充分比较。对今天的研究来说，baseline 偏少。

### e) 关键结果

- 小规模 `C5-S2-EV2` 和 `C10-S3-EV3` 上，RL stochastic gap 分别为 8.58% 和 11.81%，不如 CPLEX/VNS-TS。
- 20/30 客户时，VNS/TS 质量更好，但耗时约为 RL 的 7-10 倍。
- 40 客户以上，15 分钟限制下 RL 是唯一能求解的方法。
- 50 客户实例，RL 平均约 1.8 分钟。
- `C30-S4-EV4` 中，RL 约 40 分钟解完 100 个实例，而 VNS/TS 两小时只解 12 个。
- `C100-S12-EV12` 中，VNS/TS 两小时内无法解出实例，RL 平均约 4 分钟一个实例。

### f) 消融实验

论文没有严格完整的消融实验。它提供了可视化和算法分析，展示 attention 会关注 depot 和 charging stations，且策略会结合位置和时间窗。但没有单独去掉 graph embedding、mask、LSTM 或不同 reward 项的 ablation。

### g) 结论是否充分

论文对“速度和规模优势”的支持较强；对“大规模质量足够好”的支持较弱，因为缺少强现代启发式和真实数据对比；对“可泛化到 EVRPTW 变体”的判断更多是潜力，而不是充分实验证明。

## 5. 局限性与可改进点

### a) 论文自己承认的局限

小规模解不最优；充电决策短视；可能错过早期充电机会；完整约束没有理论保证；未来应设计单独充电决策模型、放松 full charging 假设、结合元启发式/MIP，并使用真实能耗和充电数据。

### b) 隐含问题

- 训练数据是随机仿真，不是真实路网。
- 能耗是简化线性模型。
- 服务时间被简化为常数。
- 只训练小规模再测试大规模，泛化机制不够严谨。
- 无强消融实验。
- 约束可行性主要靠 mask，边界情况风险高。
- 训练约 90 小时，对本科阶段复现不轻。

### c) 可改进方向

可以加入局部搜索修复和改进；把充电决策拆成“何时充、在哪充、充多少”；引入真实路网距离、交通时间和非线性能耗；改用 GNN/Transformer encoder；把 hard constraint violation 作为 safety layer 或 repair layer。

### d) 可能的 research ideas

1. DRL + OR-Tools repair：RL 生成初始解，OR-Tools 或 ALNS 修复时间窗和电量约束。
2. 分层策略：上层决定客户访问顺序，下层决定充电站和充电量。
3. Partial charging EVRPTW：放松 full charging，学习连续充电时间或充电量。
4. 动态 EVRPTW：客户需求、交通时间、充电站可用性实时变化时做 rolling horizon RL。
5. 约束感知 Transformer：在 attention logits 中加入可行性、slack time、电量余量和等待时间特征。

## 6. 复现与应用建议

### a) 是否开源

论文只说明使用 Python 和 TensorFlow 2.2.0 实现，没有在正文中给出 GitHub 或代码链接。

### b) 复现关键步骤

实现随机 EVRPTW instance generator；实现状态转移；实现 mask；实现 graph embedding/Structure2Vec；实现 attention + LSTM decoder；实现 REINFORCE + rollout baseline；复现 greedy/stochastic/beam search；用 CPLEX、VNS 或 OR-Tools 做 baseline。

### c) 需要准备的背景知识

需要掌握 VRP/VRPTW/EVRPTW 建模、强化学习 REINFORCE、attention/pointer network、图神经网络或 Structure2Vec、PyTorch/TensorFlow、OR-Tools、启发式算法和约束处理。

### d) 复现难度

复现难度：高。原因是模型结构、动态 mask、EVRPTW 状态转移、训练稳定性和实验 baseline 都比较复杂；训练时间也长。若只复现简化版，难度中等。

### e) 对当前科研的作用

结论：必须精读。它是 EVRP-TW + Deep RL 的直接代表作，尤其值得学习状态、动作、奖励和 mask 的设计。但不能只照搬，因为其充电决策和实验设置都有明显改进空间。

## 7. 最终总结

### a) 一句话核心思想

用注意力强化学习解 EVRPTW。

### b) 关键词

EVRPTW、Deep Reinforcement Learning、Attention Model、Graph Embedding、Masking Scheme。

### c) 读完后的行动清单

1. 复画论文 pipeline 和状态转移公式。
2. 用 OR-Tools 先实现一个小规模 EVRPTW baseline。
3. 复现简化版 RL：先不加 Structure2Vec，只做 attention + mask。
4. 重点实验充电决策失败案例，分析 late charging 问题。
5. 设计一个“RL 初始解 + 局部搜索修复”的改进方案。

### d) 是否适合放入文献综述

适合，而且应放在核心文献。理由是它直接针对 EVRPTW，提出端到端 DRL 框架，并明确讨论了时间窗、电池、充电站和大规模可扩展性。但综述中要客观指出其约束保证不足、真实场景弱、充电策略短视和 baseline 不够现代。
