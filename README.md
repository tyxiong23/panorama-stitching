# panorama-stitching 全景图像拼接

Course Project of Virtual Reality

成员：熊天翼，潘紫琪，弋紫轩

### 使用方式

~~~python
python main.py <input-dir> 
--blending [no/simple/mbb] 
--gain-compensation [no/yes]
--gain-sigma-n #gain compensation parameter
--gain-sigma-g #gain compensation parameter
~~~
输出位于`input-dir/result`

### 代码框架

~~~
工作路径
|-- inputs ##输入图片和结果
|-- src # 源代码
|-- main.py # 主程序
~~~

#### Stitcher
封装了全景拼接所需的全部功能，包括载入input图片，SIFT，相关图片的matching，并计算每个输入图片的H矩阵，匹配全景图，并最后生成结果

#### Matcher
用于通过特征点找到匹配的图片对，并得到connected-components（每个component对应一张全景图，以及全景图中各图片的相关关系）

#### PairMatch
用于表示一对匹配上的图片（A and B），可用于判断匹配是否有效（valid）、计算Homograhy矩阵

#### Optimizations

用于改进图像拼接后的效果，主要采取措施有gain compensation和multiband blending。Gain Compensation通过分别计算RGB通道中关于loss方程的最优解获得两张图片重合部分像素点的增益补偿，在后续图像生成中使用。Multiband blending通过对重合部分分频律计算融合参数，加权平均进行图像融合，达到更好的效果。

### 难点与解决方案

**1、如何实现多组图片的分别拼接？**

在输入图片分属于不同全景图时，我们在matching的过程中会查询图片之间的关联性，把每一组互相关联的图片分成不同的组（connected-component），在组内计算homography矩阵并生成最后的结果。

**2、视角选择**

在计算homography矩阵时，实际上计算的都是其余照片相对于某张基准图片（H矩阵为单位阵）的位置。在选取基准图片时，我们遍历了所有可能的图片，选取拼接图片高度最小的结果输出（这样拼接图片基本在视角正中心）。

**3、如何提升照片的拼接效果**

(1) Gain Compensation

虽然是同一个场景照出来的照片，但是可能出现不同照片光强不同的情况。此时需要对于强度进行重新计算，进行增益补偿。

根据Error Function求解最优解，可以得到每张图片在融合时所需的增益补偿：![image-20230108165957901](/Users/pzqnewmac/Desktop/VR/panorama-stitching/report-related/image-20230108165957901.png)

（其中N_ij为第i和第j个图像重合的像素点数，g_i为对第i张图片的增益，I^bar_ij为第ij张图片重合部分的光强平均）

(2) Multiband blending

多波段融合的基本思想是图像可以分解为不同频率的图像的叠加（类似于傅里叶变换），在不同的频率上，应该使用不同的权重来进行融合，在低频部分应该使用波长较宽的加权信号（例如高斯核函数中sigma比较大），在高频部分应该使用较窄的加权信号（例如高斯核函数的sigma比较小），其算法如下： 

1. 计算输入图像的高斯金字塔。如果输入图像是A,B，则计算GA0,GA1,GA2,GA3,…和GB0,GB1,GB2,GB3,…

2. 计算输入图像的拉普拉斯金字塔。记为LA0,LA1,LA2,LA3,…和LB0,LB1,LB2,LB3,…

3. 将处于同一级的拉普拉斯金字塔进行融合。例如在拼接缝两侧使用简单的线性融合。记输出图像为C，则这里得到LC0,LC1…

4. 将高层的拉普拉斯金字塔依次扩展直至和LC0相同分辨率。我们记做LC00,LC11,LC22…

5. 将4中得到的图像依次叠加，则得到最终的输出图像

### 局限性与可改进方向

1. 全景拼接之后造成的图像扭曲

可以看到，在进行全景拼接之后，虽然能够较为完整地显示场景全貌，却依然存在图像较为扭曲，且部分位置发生了型变得情况。解决这个问题可能有两种途径：从收集原始图片的角度，若能过对原始图片的拍摄提出一些要求，例如保持在一个水平线、尽量拍摄较远的事物等，则可以一定程度上解决这个问题；从算法角度，可以通过增加一步对于图片的拉伸变换等解决这一个问题

2. Blending之后出现虚幻的重影

由于有时特征点判断由于光线、景物分辨率等问题出现了识别不够准确的情况，因此在Blending之后容易出现重影的情况。面对这一问题，可以从两个角度解决。首先是改进提取图片特征点的算子；其次是改进拍摄图片的技术。


### 实验结果

#### 基础版本（无 Gain Compensation）

|选项|blending mask|输出全景图|
|--|--|--|
|no-blending|![](inputs/caoping/result/mask_0_no_blending.png)|![](inputs/caoping/result/panorama_0_no_blending.png)|
|simple-blending|![](inputs/caoping/result/mask_0.png)|![](inputs/caoping/result/panorama_0.png)|

其中blending mask 图中颜色的深浅用于区分不同图片，意在用mask的离散程度展示融合效果

#### 加强版本1: Gain Compensation比较

| 选项                 | 输出全景图                                                   |
| -------------------- | ------------------------------------------------------------ |
| no-gain-compensation | ![panorama_0_no_blending_no_gain](/Users/pzqnewmac/Desktop/VR/panorama-stitching/inputs/test/result/panorama_0_no_blending_no_gain.png) |
| gain-compensation    | ![panorama_0_no_blending](/Users/pzqnewmac/Desktop/VR/panorama-stitching/inputs/test/result/panorama_0_no_blending.png) |

可以看到，没有进行gaincompensation时，左下角图片的山体较整体呈现较亮的情况，但是进行了gain compensation后整体山体的颜色变得更加统一。

#### 加强版本2: 不同Blending效果比较



### 小组分工
- 熊天翼：完成全景图像拼接的python代码基础框架（SIFT + 特征点匹配 + matching + 拼接），实现了多图拼接和simple blending功能。
- 潘紫琪：实现全景图像拼接的优化gain compensation功能，写项目文档中的项目算法介绍，录制汇报视频
- 弋紫轩：实现多图拼接multiband blending功能，写项目文档中的案例分析部分
