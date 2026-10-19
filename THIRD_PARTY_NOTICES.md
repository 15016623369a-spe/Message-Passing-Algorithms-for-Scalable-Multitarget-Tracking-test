# 原始代码与论文来源

## BP 实验来源

本项目为 Florian Meyer 原始 MATLAB 演示的非官方 Python / Jupyter 移植与实验整理。

- 原始作者标注：`Florian Meyer, 2017, 2020`。
- 原始仓库：https://github.com/meyer-ucsd/MTT-PIEEE-18
- 原始提交：`d2e02df90d85aca5ad1120d80f8ba66946e903ca`。
- 主要实验参考文献：Meyer F, Braca P, Willett P, Hlawatsch F. A Scalable Algorithm for Tracking an Unknown Number of Targets Using Multiple Sensors[J]. IEEE Transactions on Signal Processing, 2017, 65(13): 3478–3493. DOI: 10.1109/TSP.2017.2688966.

原始 `main.m` 注释同时引用2017年论文与2018年综述，完整引用列于 `REFERENCES.bib`。
原算法与MATLAB源程序的作者署名归原作者；本项目增加Python移植、Notebook说明、数值诊断、OSPA及结果整理。
本仓库不包含原14个MATLAB文件的副本，可通过原仓库查看。

在上述源提交中未发现独立的LICENSE文件或SPDX许可声明。
本项目保留来源及原作者署名，不将上游代码标注为MIT、Apache或其他未经来源确认的许可。
论文引用和来源标注本身不构成原作者的许可或背书；需要进一步使用许可时应向原权利人确认。


## MT3 实验来源

新增的`experiments/mt3/`是Pinto等人2021年MT3实验的Notebook适配，原仓库为[JulianoLagana/MT3](https://github.com/JulianoLagana/MT3)，固定提交`c1270e1de5b8d68eab50a797d16061310fa95d97`。其43个原始文件保持不变，原作者MIT许可见[MT3/LICENSE](experiments/mt3/MT3/LICENSE)，详细范围见[MT3来源说明](experiments/mt3/THIRD_PARTY_NOTICES.md)。MT3许可不改变上述BP来源的许可状态。

MT3引用Pinto等人的*Next Generation Multitarget Trackers: Random Finite Set Methods vs Transformer-based Deep Learning*（2021），见[MT3引用信息](experiments/mt3/CITATION.cff)。BP实验继续引用Meyer等人2017年论文，见[BP引用信息](docs/BP_CITATION.cff)。
