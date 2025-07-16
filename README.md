# SittingWatch——基于Web监控摄像头的智能坐姿分析系统

## 一、项目简介

SittingWatch智能坐姿分析系统，包括**实时监测**（基于视频流）和**精确分析**（基于静态图像）两种模式，旨在帮助人们养成良好坐姿习惯，并及时筛查潜在疾病隐患。

在**实时监测**模式下，SittingWatch完全运行在**本地**，通过Web摄像头持续追踪用户姿态。在获取视频流之后，使用轻量化的**MediaPipe**模型实时检测**人体关键点的3D坐标**，包括眼、耳、肩、脊柱等。利用这些关键点的3D位置，实时计算它们之间的**相对位置关系**，然后通过设定好的**阈值**判断坐姿检测好坏，并记录在**MySQL**数据库中。

在**精确分析**模式下，SittingWatch接受一张用户的坐姿图片，**预处理**（直方图均衡化、锐化）之后，调用云端的**YOLOv8**模型进行坐姿“好”“坏”的检测。YOLO的训练数据是我用**X-AnyLabeling**标注的，它虽然实时性有限且只提供二分类，但提供了出色的**鲁棒性**，尤其是在光线暗、图片倾斜等情况下。

除了上述核心功能，Web上还实现了：1）**用户账号管理**；2）在检测到持续异常时，通过SMTP向用户邮箱**发送提醒邮件**；3）通过LLM生成坐姿数据**分析报告**。

---

## 二、环境依赖安装与运行
1. 创建并激活一个Conda环境
```python
conda create -n hunch python=3.12 -y
conda activate hunch
```
2. 安装项目依赖
- `requirements.txt`如下
```txt
Flask==3.1.1  
Flask_Cors==4.0.0  
flask_mail==0.10.0  
mediapipe==0.10.21  
numpy==1.24.2  
openai==1.90.0  
opencv_python==4.9.0.80  
pandas==1.5.3  
Requests==2.32.4
```
- 在项目根目录执行：
```bash
pip install -r requirements.txt
```
3. 运行app.py文件 
4. 运行前端：
```
cd /your/path/to/HunchedPostureScreening/frontend
python -m http.server 5002
```

---

## 三、文件组织结构

```md
HunchedPostureScreening/      # 项目根目录
│
│  
├── app.py                    # Flask应用主入口
├── requirements.txt          # Python依赖包列表
├── tree.txt                  # 目录结构记录文件
├── users.json                # 存储用户账户信息
│
├── .idea/               
│
│  # 图像处理核心功能模块(捕获→预处理→检测→分类/分析)
├── core/
│   ├── __init__.py           
│   ├── analyzer.py           # 姿势分析模块(处理视频流、图片)
│   ├── capture.py            # 摄像头视频帧捕获
│   ├── classifier.py         # 姿态异常判断（调用云端自训练大模型接口）
│   ├── detecter.py           # 通过人体关键点计算矫正参数
│   ├── preprocessing.py      # 对用户上传图像进行预处理（多种基本数字图像方法）
│   └── scheduler.py          # 任务调度、异常姿势持续检测与警报机制
│
│  # 前端
├── frontend/
│   ├── css/                  # 样式
│   │   ├── daily_report.css  
│   │   ├── index.css         
│   │   └── login.css         
│   │
│   ├── html/                 # HTML模板
│   │   ├── daily_report.html # 日报分析页面
│   │   ├── index.html        # 首页（摄像头实时监测/上传图片识别）
│   │   └── login.html        # 登录注册页面
│   │
│   └── img/                  # 静态图片资源
│
│  # 日志文件(持久化存储用于分析用户历史坐姿)
├── logs/
│   └── posture_log.csv       # 姿势信息记录(时间戳+关键值)
│
│  # 大模型调用板块
├── models/
│   └── report_generator.py   # 调用大语言模型分析日志文件生成报告（邮箱内容）
│
│ 
├── static/
│   └── tmp/                  # 临时文件目录(预处理增强和标注后的用户上传图片)
│
│  # 工具模块
└── utils/
    ├── config.py             # 配置管理(服务端口、异常通知阈值设定、smtp配置)
    └── emailer.py            # 邮件发送服务
```
