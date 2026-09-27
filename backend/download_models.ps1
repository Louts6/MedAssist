# =====================================================================
# DeepDoc 模型下载脚本（Windows / PowerShell）
#
# 本仓库未包含 ONNX 模型与 trie 编译缓存（约 330MB）：
#   - layout*.onnx / det.onnx / rec.onnx / tsr.onnx / *.model
#       来自 RAGFlow 官方 HuggingFace 仓库 InfiniFlow/deepdoc
#       （程序首次解析 PDF 时也会自动触发下载）
#   - huqie.txt.trie 是分词词典 huqie.txt 的运行时编译缓存，
#       首次启动时自动生成，无需下载
#
# 国内网络可先设置镜像：$env:HF_ENDPOINT="https://hf-mirror.com"
# =====================================================================

$ErrorActionPreference = "Stop"

# 允许通过环境变量使用国内镜像
if (-not $env:HF_ENDPOINT) { $env:HF_ENDPOINT = "https://hf-mirror.com" }
Write-Host "使用 HF 端点: $env:HF_ENDPOINT" -ForegroundColor Cyan

# 安装 huggingface_hub
python -m pip install -U huggingface_hub

# 模型落地目录：service/core/rag/res/deepdoc
$target = Join-Path $PSScriptRoot "app\service\core\rag\res\deepdoc"
New-Item -ItemType Directory -Force -Path $target | Out-Null

Write-Host "正在下载 InfiniFlow/deepdoc 模型到: $target" -ForegroundColor Cyan
python -c @"
import os
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='InfiniFlow/deepdoc',
    local_dir=r'$($target.Replace('\','\\'))',
    local_dir_use_symlinks=False,
)
print('模型下载完成')
"@

Write-Host "`n完成。huqie.txt.trie 将在服务首次启动时自动构建。" -ForegroundColor Green
