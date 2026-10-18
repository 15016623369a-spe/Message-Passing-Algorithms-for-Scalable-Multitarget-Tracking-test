# Message Passing Algorithms for Scalable Multitarget Tracking test

基于置信传播（Belief Propagation，BP）的多目标跟踪实验，提供可独立运行的 Python / Jupyter Notebook。

## 论文与代码来源

**本项目参考以下论文的实验代码进行 Python / Jupyter 转换与整理：**

> Meyer F, Braca P, Willett P, Hlawatsch F. A Scalable Algorithm for Tracking an Unknown Number of Targets Using Multiple Sensors[J]. IEEE Transactions on Signal Processing, 2017, 65(13): 3478–3493. DOI: 10.1109/TSP.2017.2688966.

- 论文：[DOI: 10.1109/TSP.2017.2688966](https://doi.org/10.1109/TSP.2017.2688966)
- 原始 MATLAB 实现：[meyer-ucsd/MTT-PIEEE-18](https://github.com/meyer-ucsd/MTT-PIEEE-18)
- 原始代码作者：**Florian Meyer（2017、2020）**
- 转换所依据的提交：[`d2e02df90d85aca5ad1120d80f8ba66946e903ca`](https://github.com/meyer-ucsd/MTT-PIEEE-18/commit/d2e02df90d85aca5ad1120d80f8ba66946e903ca)

这是非官方的学习与实验移植。仓库名称采用2018年综述 *Message Passing Algorithms for Scalable Multitarget Tracking* 的标题；
主要实验参考文献为上述2017年论文。原始 `main.m` 同时引用这两篇文章，详见 [参考文献](REFERENCES.bib) 和 [来源说明](THIRD_PARTY_NOTICES.md)。

## 快速运行

1. 安装 Python，并在 VS Code 安装 **Python** 和 **Jupyter** 扩展。
2. 克隆仓库，在项目文件夹建立虚拟环境并安装依赖：

```bash
git clone https://github.com/15016623369a-spe/Message-Passing-Algorithms-for-Scalable-Multitarget-Tracking-test.git
cd Message-Passing-Algorithms-for-Scalable-Multitarget-Tracking-test
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell 使用：.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

3. 打开 [MTT_BP_Python.ipynb](MTT_BP_Python.ipynb)，选择 `.venv` 对应的 Python 内核，点击 **全部运行**。

算法代码全部内嵌于 Notebook；不需要安装 MATLAB，也不需要加载 `bp_tracking.py`。
Notebook 在仓库中保留为空输出版本，结果运行后会显示，并写入当前工作目录的 `results/`。

也可以从终端完整执行并把带输出的 Notebook 保存到 `results/`：

```bash
python run_notebook.py
# 首次检查环境时可运行小实例（30帧、500粒子）：
python run_notebook.py --quick
```

快速实例不能代替默认规模实验。`results/` 已加入 `.gitignore`，避免每次运行都改动仓库中的 Notebook 或提交本机运行信息。

## 默认实验设置

| 参数 | 数值 |
|---|---:|
| 仿真帧数 / 帧间隔 | 200 / 1秒 |
| 真实目标总数 / 传感器数 | 5 / 2 |
| 每个潜在目标的粒子数 | 10000 |
| 随机种子 | 1 |
| 单传感器探测概率 | 0.9 |
| 每帧每传感器平均杂波数 | 5 |
| 距离 / 方位角噪声标准差 | 25米 / 0.5度 |
| 输出存在概率阈值 | 严格大于0.5 |
| 附加位置OSPA参数 | p=2，c=200米 |

`QUICK_CHECK=False` 为默认完整实验。可在参数单元格修改 `SEED`、粒子数等设置；修改后应从头运行。
状态为 `[x, y, vx, vy]`；方位角采用度数，从正y轴起算，使用 `atan2(dx, dy)`。

## 示例结果

以下来自一次固定种子1、200帧、10000粒子的运行，示例CSV和摘要位于 [examples/](examples/)。

| 指标 | 本次示例 |
|---|---:|
| 帧级数量完全正确 | 191/200（95.5%） |
| 输出数量MAE | 0.045 |
| 期望数量MAE | 0.05197 |
| 全程平均位置OSPA | 14.92米 |
| 所有BP更新满足数值停止条件 | 是 |
| 最大BP迭代次数 | 740 |

数量正确率按每帧输出目标数是否等于真实数量计算；它不是逐目标检测率或身份识别准确率。
OSPA综合匹配后的位置误差与数量差惩罚，本实现只评价二维位置，不衡量速度或ID切换。
示例核心实验时间约4.13秒，仅供记录；运行时间随硬件、依赖版本和系统负载变化。

![真实轨迹与估计轨迹](docs/images/trajectories.png)

![目标数量估计](docs/images/target_counts.png)

![位置OSPA及其分量](docs/images/ospa.png)

## 文件说明

| 文件 | 用途 |
|---|---|
| `MTT_BP_Python.ipynb` | 中文分节说明、完整内嵌算法、运行、图表、OSPA与结果保存 |
| `bp_tracking.py` | 与Notebook算法对应的Python模块，便于阅读和导入 |
| `run_notebook.py` | 用当前解释器启动新内核并执行Notebook |
| `requirements.txt` | 运行和执行Notebook所需依赖 |
| `examples/` | 示例逐帧指标与摘要，不参与算法输入 |
| `docs/images/` | 示例数据的结果图 |
| `docs/IMPLEMENTATION.md` | 原MATLAB文件对应关系及实现边界 |
| `REFERENCES.bib` / `CITATION.cff` | 论文引用信息 |
| `THIRD_PARTY_NOTICES.md` | 原始作者、来源与许可说明 |

## 复现范围

保留原演示的运动和量测模型、默认参数、BP关联方程、顺序多传感器更新、系统重采样、出生及剪枝流程。
新增中文说明、收敛诊断、结果CSV和仅位置OSPA。
Python和MATLAB随机数生成器及抽样顺序不同，因此即使种子相同也不应逐点相等。
尚未通过MATLAB引擎对同一输入逐值比较，也未复现论文全部对比方法、多随机种子统计或大规模实验。
BP达到数值停止条件不等于证明其近似后验是精确的；单次示例也不足以说明方法优于其他算法。

已验证的运行环境为 Python 3.14.7、NumPy 2.5.2、SciPy 1.18.1、Matplotlib 3.11.2、pandas 3.0.6。
依赖文件给出最低版本约束；其他版本的运行与数值一致性需在对应环境检验。

## 引用与署名

使用本实验时请引用上述2017年论文，并保留原始代码仓库与原作者署名。
另参阅 [REFERENCES.bib](REFERENCES.bib)。本仓库未添加覆盖上游代码的MIT、Apache等再授权声明；
上游来源和许可状态见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
