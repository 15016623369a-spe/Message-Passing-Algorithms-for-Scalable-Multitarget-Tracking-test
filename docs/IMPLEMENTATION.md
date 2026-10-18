# 实现对应与使用边界

## MATLAB与Python对应关系

| MATLAB 文件 | 本笔记本函数/部分 |
|---|---|
| `main.m` | 参数单元格、`run_experiment` 与实验运行 |
| `getStartStates.m`、`getSensorPositions.m` | `get_start_states`、`get_sensor_positions` |
| `generateTrueTracks.m` | `generate_true_tracks`、`transition_matrices` |
| `generateTrueMeasurements.m` | `generate_true_measurements` |
| `generateClutteredMeasurements.m` | `generate_cluttered_measurements` |
| `performPrediction.m` | `perform_prediction` |
| `introduceNewPTs.m` | `introduce_new_pts`、`calculate_constants_uniform`、`sample_from_likelihood` |
| `evaluateMeasurements.m` | `evaluate_measurements` |
| `performDataAssociationBP.m` | `perform_data_association_bp` |
| `updatePTs.m` | `update_pts`、`resample_systematic` |
| `trackerBP.m` | `tracker_bp` |
| `trackFormation.m` | `track_formation` |
| `showResults.m` | 轨迹、数量、单帧图与可选动画 |

**保留：**原始模型、默认参数、BP 方程、粒子均值估计、系统重采样、出生标签、传感器更新顺序与剪枝阈值。
**实现差异：**Python 与 MATLAB 随机序列不同；加入有限值检查、BP 收敛记录和接近零分母的数值保护；绘图改为笔记本内显示。
新生目标初始化仍按作者的似然采样实现，不额外增加极坐标 Jacobian 或更改出生模型。
OSPA、结果 CSV 和诊断是附加检查。未执行 MATLAB 引擎作同输入逐值比对，未复现论文全部实验表格。

原始 MATLAB 作者：**Florian Meyer（2017、2020）**；[原始代码仓库](https://github.com/meyer-ucsd/MTT-PIEEE-18)。

对应论文：

1. F. Meyer, P. Braca, P. Willett, F. Hlawatsch. *A Scalable Algorithm for Tracking an Unknown Number of Targets Using Multiple Sensors*. IEEE TSP 65, 3478–3493, 2017. [DOI](https://doi.org/10.1109/TSP.2017.2688966)
2. F. Meyer, T. Kropfreiter, J. L. Williams, R. A. Lau, F. Hlawatsch, P. Braca, M. Z. Win. *Message Passing Algorithms for Scalable Multitarget Tracking*. Proceedings of the IEEE 106, 221–259, 2018. [DOI](https://doi.org/10.1109/JPROC.2018.2789427)
