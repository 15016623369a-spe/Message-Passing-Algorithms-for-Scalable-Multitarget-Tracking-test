# MT3：Transformer 多目标跟踪实验

本目录将 [JulianoLagana/MT3](https://github.com/JulianoLagana/MT3) 整理为可在 VS Code/Jupyter 逐格运行的 Notebook，包含方法机理、训练、权重保存/重载、独立测试、GOSPA分解、图表与实验报告。模型、损失和仿真模块保留作者源码。

**对应论文：** Pinto J, Hess G, Ljungbergh W, Xia Y, Svensson L, Wymeersch H. *Next Generation Multitarget Trackers: Random Finite Set Methods vs Transformer-based Deep Learning*. 2021. [arXiv:2104.00734](https://arxiv.org/abs/2104.00734). 原始提交：`c1270e1de5b8d68eab50a797d16061310fa95d97`。

| 入口 | 内容 |
|---|---|
| [MT3_Reproduction.ipynb](MT3_Reproduction.ipynb) | 中文说明、方法公式及完整实验流程 |
| [方法机理](docs/METHOD.md) | 注意力、two-stage查询、迭代细化、集合匹配、对比学习和GOSPA |
| [实验结果报告](docs/EXPERIMENT_REPORT.md) | 实测数据、配置差异、结果解释与结论边界 |
| [Task 1示例](examples/task1_short/) / [Task 2示例](examples/task2_short/) | 真实运行的配置、逐窗口CSV、汇总、训练曲线和场景图 |
| [原始代码](MT3/) / [来源清单](SOURCE_MANIFEST.json) | 43个上游文件及SHA256；模型源码未修改 |

## 运行

在已克隆仓库的终端中执行（推荐Python 3.12）：

```bash
cd experiments/mt3
python3 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-notebook.txt
python -m ipykernel install --user --name mt3-experiment --display-name "Python (MT3)"
```

打开本目录的Notebook，选择 **Python (MT3)** 内核，点击“全部运行”。可以从仓库根目录或本实验目录启动，入口会自动定位`MT3/`源码。需要保留本目录完整结构；Notebook调用本地原始模块，不是独立单文件实现。BP与MT3依赖分开，根目录`requirements.txt`不包含MT3所需的PyTorch。

也可以用当前解释器在新内核完整执行：

```bash
python run_notebook.py
python run_notebook.py --task task2 --steps 2 --batch-size 1 --eval-windows 2 --output Task2_validation.executed.ipynb
```

默认`TASK='task1', PROFILE='quick'`，原始18118165参数模型不缩小；从随机权重优化20步、batch=2、测试8个窗口。`PROFILE='full'`加载原YAML的100万步、batch=32、1000测试窗口，适用于长期训练；**它不是“论文参数模式”**。原配置与论文有实质差异，见报告。

需要继续训练时设置`CHECKPOINT_PATH`及`RESUME_TRAINING=True`；只评估已有匹配检查点时设置`TRAIN_STEPS_OVERRIDE=0`。恢复包含模型、优化器和调度器，未保存数据生成器RNG状态，因此不保证与未中断训练逐位一致。检查点格式由本Notebook生成；其他权重需先核对键名、架构与数据配置。

每次完整运行在`results_mt3/<task>_<profile>_<时间戳>/`生成配置JSON、训练CSV、逐窗口评估CSV、指标汇总、3张图、第一窗口NPZ与最终`.pt`检查点。权重含优化器状态约208MB，默认不提交；本仓库没有训练充分的预训练权重。Notebook提交为空输出版本，已保存结果见examples。

## 已验证结果及边界

Task 1：20次优化、8个测试窗口，MT3平均GOSPA=2.5；Task 2：2次优化、2个测试窗口，平均GOSPA=9。两组所有窗口均未输出超过0.9阈值的目标，误差全为漏检。训练、保存/重新加载、独立评估通过检查，但尚未完成充分训练或论文精度复现。

两组预算不同，不能直接比较效果；没有运行PMBM、δ-GLMB、跨窗口ID指标或多种训练种子的统计。原Random参考在该阈值下输出空集合，oracle使用真实关联ID。完整证据与解释见[报告](docs/EXPERIMENT_REPORT.md)。

这是本仓库新增的 **MT3实验**；根目录[BP实验](../../MTT_BP_Python.ipynb)保留其原论文与代码来源。MT3使用Transformer和监督学习，BP实验使用粒子与置信传播，两者算法及指标场景不同。

## 署名与许可

原MT3作者MIT许可完整保留于[MT3/LICENSE](MT3/LICENSE)，其范围为该上游实现。请引用本目录[CITATION.cff](CITATION.cff)所列MT3论文并注明原仓库；其他来源与新增整理说明见[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
