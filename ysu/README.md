# 燕山大学教务问答助手 - 基于ChatGLM3-6B的领域大模型微调

## 项目简介

本项目旨在构建一个针对燕山大学教务处信息的智能问答系统。通过采用网络爬虫技术从[燕山大学教务处官网](https://jwc.ysu.edu.cn/index.htm)采集公开的规章制度、通知公告等文本数据，经过清洗和处理后，构建成高质量的问答（Q&A）数据集。最终，利用该数据集对 ChatGLM3-6B 大语言模型进行高效参数微调（LoRA），使其掌握燕山大学教务领域的专业知识，能够准确回答师生的相关问题。

## 项目结构

```
.
├── scraper/              # 存放爬虫脚本
├── data/                 # 存放原始数据、处理脚本和最终数据集
├── saves/                # 存放训练好的模型适配器（LoRA Checkpoints）       
├── requirements.txt      # 项目Python环境依赖文件
└── README.md             # 项目说明文件
```

* **scraper/**: 数据获取模块，负责从官网爬取原始文本数据。
* **data/**: 数据处理模块，包含原始数据、数据清洗与格式化脚本，以及最终生成的 `ysu_dataset.json` 训练数据集。
* **saves/**: 训练成果模块，包含了使用LoRA方法微调后生成的模型适配器。

## 环境配置

本项目在以下环境测试通过：
- **操作系统**: Windows 10
- **Python版本**: 3.11
- **核心框架**: PyTorch 2.5.1 (CUDA 12.1), Transformers 4.50.0, LLaMA Factory

**复现步骤：**

1.  确保您的系统已正确安装NVIDIA驱动、CUDA 12.1以及Conda。
2.  创建一个新的Conda环境：
    ```bash
    conda create -n ysu_qa_env python=3.11 -y
    conda activate ysu_qa_env
    ```
3.  安装PyTorch（必须先执行此步）：
    ```bash
    pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cu121](https://download.pytorch.org/whl/cu121)
    ```
4.  安装 LLaMA Factory 及其所有依赖：
    * 首先，克隆或下载 LLaMA Factory 源代码并解压。
    * 然后进入 `LLaMA-Factory` 目录，运行以下命令安装：
    ```bash
    # (推荐) 安装完全体，包含所有可选依赖
    pip install -e ".[full]" -i [https://pypi.tuna.tsinghua.edu.cn/simple](https://pypi.tuna.tsinghua.edu.cn/simple)
    # 或者根据 requirements.txt 安装核心依赖
    pip install -r requirements.txt -i [https://pypi.tuna.tsinghua.edu.cn/simple](https://pypi.tuna.tsinghua.edu.cn/simple)
    ```

## 使用说明

### 步骤一：数据获取与处理
1.  进入 `scraper` 目录，运行爬虫脚本，获取原始数据。
2.  进入 `data` 目录，运行数据处理脚本，生成最终的 `ysu_dataset.json`。

### 步骤二：模型下载
为了进行离线训练，请先将模型下载到本地。
```bash
# 需要先安装 git-lfs (git lfs install)
git clone [https://hf-mirror.com/THUDM/chatglm3-6b-base](https://hf-mirror.com/THUDM/chatglm3-6b-base) /path/to/your/models/chatglm3-6b-base
```

### 步骤三：模型微调
1.  进入 `LLaMA-Factory` 目录，通过以下命令启动WebUI：
    ```bash
    python -m llamafactory.cli webui
    ```
2.  在 `Train` 页面进行如下核心配置：
    - **Model path**: 指向您在**步骤二**中下载的本地模型路径。
    - **Dataset**: 选择您处理好的数据集（例如 `ysu_dataset.json`）。
    - **Finetuning method**: `lora`
    - **Quantization bit**: `4`
    - **Evaluation strategy**: `no` (重要：避免版本兼容性问题)
    - **Val size**: `0` (重要：避免版本兼容性问题)
3.  点击 `Train` 开始训练。训练结果将保存在 `saves` 目录中。

### 步骤四：模型验证
1.  在WebUI中，切换到 `Chat` 标签页。
2.  配置如下：
    - **Model path**: 依然指向本地的基础模型路径。
    - **Checkpoint path**: 指向您在**步骤三**中训练产出的 `saves/glm3_ysu_lora` 
    - 通过网盘分享的文件：glm3_ysu_lora
      链接: https://pan.baidu.com/s/1lbSZ99e3M50uNjXEhtbi0w?pwd=iysu 提取码: iysu 
      --来自百度网盘超级会员v8的分享
3.  点击 `Start` 加载模型，即可在下方的对话框中进行问答测试。

## 实验结果

| 指标 (Metric)                       | 值 (Value)                    |
| ----------------------------------- | ----------------------------- |
| 最终训练损失 (train_loss)           | **1.565**                     |
| 总训练时长 (train_runtime)          | **1214.06 秒 (约 20.2 分钟)** |
| 每秒处理样本数 (samples_per_second) | 1.614                         |
| 硬件环境                            | NVIDIA GeForce RTX 3060       |

### 训练过程
模型经过3个Epoch的微调，损失（Loss）变化如下图所示，呈现稳定下降趋势，证明模型有效学习了领域知识。
![training_loss](D:\01Code\Project\Python\Orientation\ChatGLM\LLaMA-Factory\saves\ChatGLM3-6B-Base\lora\glm3_ysu_lora\training_loss.png)

### 验证效果
通过与微调后的模型进行交互式问答，检验其在燕大教务领域的表现。

**优秀回答 (Good Case):**

> **问**: 燕山大学的本科生什么时候可以申请转专业？
> 	**答**: 根据规定，普通本科生可在大学一年级第二学期申请转专业.

