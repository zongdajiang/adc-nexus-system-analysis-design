# 重建与核验

## 直接阅读

`分析设计文档/`已提供审核后的PDF和ZIP。下载后即可阅读，无须先安装Python、LaTeX或绘图软件。

## 验证已发布文件

Python环境安装`tools/requirements.txt`中的依赖后，可执行：

```powershell
python tools/verify-release.py
```

该检查核对文件校验和、报告83页、55张图号清单、数据库规模、两个UML图册、十张ERD及相对链接。它不重新绘制或重新编译，不替代目视检查或业务验收。

审核过的修改若需要重新生成校验清单，使用`python tools/verify-release.py --write-manifest`；该模式按仓库规则统一文本为LF换行，再更新校验记录和SHA-256清单，确保Git上传前后内容一致。

## 编辑与重建主报告

保持整个目录结构，从`report/main.tex`修改。报告使用Windows中文字体，图版工具还需相应字体；其他平台需自行配置兼容字体。Tectonic构建使用本机已有资源缓存，首次配置可能需要另行联网准备缓存。

```powershell
python -m pip install -r tools/requirements.txt
.\tools\build-refined-edition.ps1 -Python (Get-Command python).Source -Tectonic (Get-Command tectonic).Source
```

当前脚本仅重建四张状态图与主报告，不重新设计其他已审核图。主报告写入固定发布路径`分析设计文档/ADC_Nexus_主文档.pdf`，再执行结构及布局检查并更新文件校验和。

`report/main.pdf`、编译日志、辅助文件和整页渲染缓存均不提交Git；它们可在本机保留。旧版本差异检查的结果保存在`qa/本轮修订保护检查.json`，原始差异检查依赖本地上版目录，不作为公开仓库的重建前提。

## 更改原尺寸图版时

全景、内部序列与ERD含正文页码。若编辑导致图号或页码改变，须同步相应母版及页码，再重新编译；不能只更新主报告中的数字。相关脚本为：

- `figure_registry.py`：从正文生成统一图号清单。
- `render_standard_overviews.py`：现状、改进和系统用例全景。
- `render-analysis-plates.py`、`render-class-atlas.py`：图版及类图图册。
- `number_native_plates.py`、`bundle-analysis-plates.py`：正式题注、页码及合订本。
- `verify-report.py`、`verify-diagram-layout.py`：正文结构、题注和已编码的布局规则。

生成数据目录或关系说明时，还应保留已经人工精修的正文，不直接用初始模板覆盖。完成后再渲染PDF检查。

## 模型与文件说明

`database/`是常用定义的直接入口，完整建模上下文保存在`data-design/`。两处的同名模型和DDL应保持相同校验和。初始字段字典专项PDF保留原始建模日期，与最新主报告分工不同，不用于判定当前图号或功能实现状态。

`skills/`只包含本项目重建所需的运行脚本，不是包含参考材料的完整本地Codex技能安装包。`.drawio`保留可编辑图元，但部分连接按绝对坐标导出；需要稳定整体重排时优先修改语义模型后生成。
