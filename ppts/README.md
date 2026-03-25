# PPTX Slides Extractor

这个项目用于批量读取 `ppts/` 目录下的 `.pptx` 文件，提取每一页的标题和正文文本，并将结果保存为 `data/slides.json`。

## 项目结构

```text
extract_slides/
├─ extract_slides.py
├─ ppts/
│  ├─ README.md
│  └─ *.pptx
└─ data/
   └─ slides.json
```

## 功能说明

- 扫描 `ppts/` 目录下的所有 `.pptx` 文件
- 提取每一页的标题和正文
- 输出 JSON 文件到 `data/slides.json`
- 每条记录包含以下字段：
  - `ppt文件名`
  - `页码`
  - `标题`
  - `正文`

## 运行方式

在项目根目录执行：

```powershell
python extract_slides.py
```

脚本默认使用相对于自身的位置：

- 输入目录：`./ppts`
- 输出文件：`./data/slides.json`

这意味着整个项目文件夹可以移动到别的路径，脚本仍然可以正常运行，不依赖固定绝对路径。

## 可选参数

你也可以手动指定输入目录和输出路径：

```powershell
python extract_slides.py --input-dir ./ppts --output ./data/slides.json
```

也支持传入其他目录：

```powershell
python extract_slides.py --input-dir D:\SomeFolder\ppts --output D:\SomeFolder\data\slides.json
```

## 输出示例

```json
[
  {
    "ppt文件名": "example.pptx",
    "页码": 1,
    "标题": "课程介绍",
    "正文": "这是第一页的主要内容。"
  }
]
```

## 使用说明

1. 把需要处理的 `.pptx` 文件放到 `ppts/` 目录下。
2. 运行 `python extract_slides.py`。
3. 在 `data/slides.json` 中查看结果。

## 注意事项

- 目前脚本主要提取幻灯片中的文本框和表格文本。
- 如果某一页没有识别到明确标题，脚本会尝试把第一段正文当作标题。
- 如果 `ppts/` 目录下没有 `.pptx` 文件，程序会输出空数组 `[]`。
- 如果某个文件损坏或不是标准 `.pptx`，脚本会跳过该文件并继续处理其他文件。
